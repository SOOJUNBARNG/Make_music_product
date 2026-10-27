#!/usr/bin/env bash
# GCP の L4 GPU VM で ACE-Step 1.5 を動かし、要件ファイルの全曲を生成する。
#
#   infra/gcp.sh enable      Compute Engine API を有効化
#   infra/gcp.sh quota       L4 GPU の割り当てを確認
#   infra/gcp.sh create      VM を作成 (空きの無いゾーンは飛ばして次のゾーンを試す)
#   infra/gcp.sh setup       VM に ACE-Step 1.5 とモデルを入れる (初回のみ・再実行しても安全)
#   infra/gcp.sh run [引数]  コードと要件ファイルを送って生成開始 (例: run --priority 1)
#   infra/gcp.sh status      VM の状態と生成ログの末尾を表示
#   infra/gcp.sh fetch       生成した WAV を手元の music-source/ にコピー
#   infra/gcp.sh ssh         VM にログイン
#   infra/gcp.sh stop        VM を停止 (ディスク代だけかかる)
#   infra/gcp.sh delete      VM をディスクごと削除 (課金が完全に止まる)
#   infra/gcp.sh spot on|off 既存 VM を Spot / 通常料金に切り替える (VM 停止中に実行)
#
# 設定は infra/gcp.env。gcloud の既定プロジェクトは変更せず、毎回 --project を付ける。
# setup・run・fetch・ssh が失敗したとき、setup が終わったときは VM を自動で停止する
# (止めたくないときは KEEP_RUNNING=true を付ける)。
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

# 環境変数で渡した値を gcp.env より優先する
_overrides="$(env | grep -E '^(PROJECT|ZONE|ZONE_CANDIDATES|VM_NAME|MACHINE_TYPE|SPOT|DISK_SIZE_GB|IMAGE_FAMILY|IMAGE_PROJECT|ACESTEP_REPO|AUTO_SHUTDOWN|KEEP_RUNNING)=' || true)"
# shellcheck source=gcp.env
source "$HERE/gcp.env"
while IFS= read -r kv; do [[ -n "$kv" ]] && export "${kv?}"; done <<< "$_overrides"

# create で実際に VM を作れたゾーンを覚えておき、以降のコマンドはそのゾーンを使う
ZONE_FILE="$HERE/.vm-zone"
ZONE_FROM_ENV=0
if grep -q '^ZONE=' <<< "$_overrides"; then ZONE_FROM_ENV=1; fi
if (( ! ZONE_FROM_ENV )) && [[ -s "$ZONE_FILE" ]]; then ZONE="$(cat "$ZONE_FILE")"; fi

REGION="${ZONE%-*}"
REMOTE_DIR="makemusic"           # VM のホーム直下
ACESTEP_DIR="ACE-Step-1.5"
KEEP_RUNNING="${KEEP_RUNNING:-false}"

CMD=""             # 実行中のサブコマンド
STARTED_HERE=0     # このコマンドで VM を起動したか
GEN_STARTED=0      # run で VM 上の生成を開始できたか

gc() { gcloud --project "$PROJECT" "$@"; }
remote() { gc compute ssh "$VM_NAME" --zone "$ZONE" --quiet --command "$1"; }
log() { printf '\033[1m==> %s\033[0m\n' "$*"; }
die() { printf 'エラー: %s\n' "$*" >&2; exit 1; }

vm_status() { gc compute instances describe "$VM_NAME" --zone "$ZONE" --format='value(status)' 2>/dev/null || true; }

# 起動直後は SSH がまだ受け付けないので、つながるまで待つ (最大 5 分)
wait_ssh() {
  local i
  for i in $(seq 1 30); do
    [[ "$(vm_status)" == RUNNING ]] || die "VM が止まりました (状態: $(vm_status))"
    if gc compute ssh "$VM_NAME" --zone "$ZONE" --quiet --ssh-flag="-o ConnectTimeout=10" --command true >/dev/null 2>&1; then
      return 0
    fi
    (( i == 1 )) && echo "VM の SSH が使えるようになるのを待っています..."
    sleep 10
  done
  die "VM に SSH で接続できません (5 分待ちました)。少し待ってから同じコマンドを再実行してください"
}

ensure_running() {
  local st; st="$(vm_status)"
  [[ -n "$st" ]] || die "VM $VM_NAME がありません。先に infra/gcp.sh create を実行してください"
  if [[ "$st" != "RUNNING" ]]; then
    log "VM を起動します ($st → RUNNING)"
    gc compute instances start "$VM_NAME" --zone "$ZONE"
    STARTED_HERE=1
  fi
  wait_ssh
}

cmd_enable() {
  log "Compute Engine API を有効化 ($PROJECT)"
  gc services enable compute.googleapis.com
}

# region / project の割り当てから 1 つの指標の上限と使用量を出す
quota_of() {  # $1=regions|project  $2=metric
  if [[ "$1" == regions ]]; then
    gc compute regions describe "$REGION" --format=json
  else
    gc compute project-info describe --format=json
  fi | python3 -c '
import json, sys
metric = sys.argv[1]
for q in json.load(sys.stdin).get("quotas", []):
    if q["metric"] == metric:
        print(int(q["limit"]), int(q["usage"]))
        break
else:
    print("0 0")
' "$2"
}

cmd_quota() {
  local l4_metric="NVIDIA_L4_GPUS"
  [[ "$SPOT" == true ]] && l4_metric="PREEMPTIBLE_NVIDIA_L4_GPUS"
  local all_limit all_usage l4_limit l4_usage ok=1
  read -r all_limit all_usage <<< "$(quota_of project GPUS_ALL_REGIONS)"
  read -r l4_limit l4_usage <<< "$(quota_of regions "$l4_metric")"
  printf '%-34s 上限 %3s  使用中 %3s\n' "GPUS_ALL_REGIONS (全体)" "$all_limit" "$all_usage"
  printf '%-34s 上限 %3s  使用中 %3s\n' "$l4_metric ($REGION)" "$l4_limit" "$l4_usage"
  local short=()
  if (( all_limit - all_usage < 1 )); then ok=0; short+=("「GPUS_ALL_REGIONS」"); fi
  if (( l4_limit - l4_usage < 1 )); then ok=0; short+=("「${l4_metric}」(リージョン ${REGION})"); fi
  if (( ok )); then
    echo "OK: L4 を 1 枚使えます"
  else
    cat <<EOF

足りない割り当て: ${short[*]}
上限を 1 以上にする申請をしてください (承認まで数分〜数日):
  https://console.cloud.google.com/iam-admin/quotas?project=${PROJECT}
EOF
    return 1
  fi
}

pick_image_family() {
  if [[ -n "$IMAGE_FAMILY" ]]; then echo "$IMAGE_FAMILY"; return; fi
  local fam
  fam="$(gc compute images list --project "$IMAGE_PROJECT" --no-standard-images \
          --filter='family~^common-cu12 AND family~ubuntu-2204' \
          --sort-by=~creationTimestamp --limit=1 --format='value(family)')"
  [[ -n "$fam" ]] || die "Deep Learning VM のイメージが見つかりません。gcp.env の IMAGE_FAMILY を指定してください"
  echo "$fam"
}

cmd_create() {
  [[ -z "$(vm_status)" ]] || die "VM $VM_NAME はすでにあります (ゾーン: $ZONE, 状態: $(vm_status))"
  local family; family="$(pick_image_family)"
  local spot_args=()
  [[ "$SPOT" == true ]] && spot_args=(--provisioning-model=SPOT --instance-termination-action=STOP)
  # ZONE を環境変数で指定したときはそのゾーンだけ、それ以外は候補を順に試す
  local zones="$ZONE" z out
  (( ZONE_FROM_ENV )) || zones="${ZONE_CANDIDATES:-$ZONE}"
  for z in $zones; do
    log "VM を作成: $VM_NAME ($MACHINE_TYPE, $z, spot=$SPOT, image=$family)"
    if out="$(gc compute instances create "$VM_NAME" \
        --zone "$z" \
        --machine-type "$MACHINE_TYPE" \
        --maintenance-policy TERMINATE \
        ${spot_args[@]+"${spot_args[@]}"} \
        --image-family "$family" --image-project "$IMAGE_PROJECT" \
        --boot-disk-size "${DISK_SIZE_GB}GB" --boot-disk-type pd-balanced \
        --metadata install-nvidia-driver=True \
        --scopes cloud-platform 2>&1)"; then
      # ディスクがイメージより大きいという警告は、Deep Learning VM が起動時に自動で広げるので無視してよい
      grep -vE "^WARNING: Some requests generated warnings|^ - Disk size: .* is larger than image size|resize the root repartition|add-persistent-disk#resize_pd" <<< "$out" || true
      echo "$z" > "$ZONE_FILE"
      echo "作成しました (ゾーン: $z)。以降のコマンドは自動でこのゾーンを使います"
      echo "ドライバのインストールに数分かかるので、少し待ってから infra/gcp.sh setup を実行してください"
      return 0
    fi
    if grep -qE "ZONE_RESOURCE_POOL_EXHAUSTED|does not have enough resources" <<< "$out"; then
      echo "→ $z は今 L4 の空きがありません。次のゾーンを試します"
      continue
    fi
    printf '%s\n' "$out" >&2
    die "VM の作成に失敗しました (ゾーン: $z)"
  done
  die "どのゾーン ($zones) にも今 L4 の空きがありません。時間をおいて (数十分〜数時間) もう一度 infra/gcp.sh create を実行してください"
}

cmd_setup() {
  ensure_running
  log "VM に ACE-Step 1.5 とモデルを入れます (初回は 10〜20 分ほど)"
  remote "$(cat <<EOF
set -euo pipefail
for i in \$(seq 1 60); do nvidia-smi >/dev/null 2>&1 && break; echo 'GPU ドライバの準備を待っています...'; sleep 10; done
nvidia-smi --query-gpu=name,memory.total --format=csv
command -v uv >/dev/null || curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="\$HOME/.local/bin:\$PATH"
[ -d $ACESTEP_DIR ] || git clone $ACESTEP_REPO $ACESTEP_DIR
cd $ACESTEP_DIR && git pull --ff-only && uv sync
uv run acestep-download
uv run acestep-download --model acestep-v15-xl-turbo
echo SETUP_OK
EOF
)"
}

cmd_run() {
  ensure_running
  log "コードと要件ファイルを送ります"
  local tmpdir; tmpdir="$(mktemp -d)"
  local tarball="$tmpdir/makemusic.tgz"
  tar -czf "$tarball" -C "$ROOT" --exclude '__pycache__' make_music.py music_requirements.txt src
  gc compute scp "$tarball" "$VM_NAME:makemusic.tgz" --zone "$ZONE" --quiet
  rm -rf "$tmpdir"

  local args="" a
  for a in "$@"; do args+=" $(printf '%q' "$a")"; done
  local shutdown_cmd=":"
  [[ "$AUTO_SHUTDOWN" == true ]] && shutdown_cmd="sudo shutdown -h now"

  log "生成を開始します (ログ: ~/$REMOTE_DIR/run.log)"
  remote "$(cat <<EOF
set -euo pipefail
mkdir -p $REMOTE_DIR && tar -xzf makemusic.tgz -C $REMOTE_DIR && rm makemusic.tgz
cd $REMOTE_DIR
if pgrep -f 'make_music.py' >/dev/null; then echo 'すでに生成中です'; exit 0; fi
nohup bash -c '~/$ACESTEP_DIR/.venv/bin/python make_music.py music_requirements.txt --acestep-root ~/$ACESTEP_DIR -v$args; echo "EXIT=\$?"; $shutdown_cmd' >> run.log 2>&1 < /dev/null &
echo 開始しました
EOF
)"
  GEN_STARTED=1
  echo "進み具合: infra/gcp.sh status / 終わったら: infra/gcp.sh fetch"
  [[ "$AUTO_SHUTDOWN" == true ]] && echo "生成が終わると VM は自動で停止します"
  return 0
}

cmd_status() {
  local st; st="$(vm_status)"
  echo "VM $VM_NAME: ${st:-なし}"
  [[ "$st" == RUNNING ]] || return 0
  remote "cd $REMOTE_DIR 2>/dev/null && tail -n 20 run.log; ls music-source 2>/dev/null | grep -c '\.wav\$' | sed 's/^/完成した曲: /'" || true
}

cmd_fetch() {
  ensure_running
  mkdir -p "$ROOT/music-source"
  log "WAV を $ROOT/music-source/ にコピーします"
  gc compute scp --zone "$ZONE" --quiet "$VM_NAME:$REMOTE_DIR/music-source/*.wav" "$ROOT/music-source/"
  echo "手元の曲数: $(find "$ROOT/music-source" -maxdepth 1 -name '*.wav' | wc -l | tr -d ' ')"
}

cmd_ssh() { ensure_running; gc compute ssh "$VM_NAME" --zone "$ZONE"; }
cmd_stop() { log "VM を停止"; gc compute instances stop "$VM_NAME" --zone "$ZONE"; }
cmd_delete() {
  read -r -p "VM $VM_NAME をディスクごと削除します。生成した曲は fetch 済みですか? [y/N] " yn
  [[ "$yn" == [yY] ]] || { echo 中止しました; return 1; }
  gc compute instances delete "$VM_NAME" --zone "$ZONE" --quiet
  rm -f "$ZONE_FILE"
}

cmd_spot() {
  local mode="${1:-}" st
  case "$mode" in
    on)  local sched=(--provisioning-model=SPOT --instance-termination-action=STOP) ;;
    off) local sched=(--provisioning-model=STANDARD --clear-instance-termination-action) ;;
    *) die "infra/gcp.sh spot on (Spot) または infra/gcp.sh spot off (通常料金) を指定してください" ;;
  esac
  st="$(vm_status)"
  [[ -n "$st" ]] || die "VM $VM_NAME がありません"
  if [[ "$st" != TERMINATED ]]; then
    log "切り替えのため VM を停止します"
    gc compute instances stop "$VM_NAME" --zone "$ZONE"
  fi
  log "VM を $([[ $mode == on ]] && echo Spot || echo 通常料金) に切り替えます"
  gc compute instances set-scheduling "$VM_NAME" --zone "$ZONE" "${sched[@]}"
  echo "切り替えました。gcp.env の SPOT も合わせて変えておくと、次に create するときも同じ設定になります"
}

# Spot で回収 (preempted) されたかを、直近 15 分の操作履歴から調べる
recently_preempted() {
  local since; since="$(date -u -v-15M +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date -u -d '15 min ago' +%Y-%m-%dT%H:%M:%SZ)"
  [[ -n "$(gc compute operations list \
      --filter="targetLink~/instances/$VM_NAME\$ AND operationType=compute.instances.preempted AND insertTime>=$since" \
      --format='value(insertTime)' --limit=1 2>/dev/null)" ]]
}

# 失敗したら VM を止めて、動きっぱなしの課金を防ぐ
finish() {
  local rc=$?
  trap - EXIT
  case "$CMD" in setup|run|fetch|ssh) ;; *) exit "$rc" ;; esac
  local st reason=""
  st="$(vm_status)"
  if [[ "$st" == RUNNING ]]; then
    if (( rc != 0 )); then
      # fetch・ssh は、もともと動いていた VM (生成中かもしれない) は止めない
      if [[ "$CMD" == setup ]] || { [[ "$CMD" == run ]] && (( ! GEN_STARTED )); } || (( STARTED_HERE )); then
        reason="失敗したので"
      else
        echo "VM は動いたままです (生成中かもしれないため止めていません)。不要なら infra/gcp.sh stop で止めてください"
      fi
    elif [[ "$CMD" == setup ]]; then
      reason="セットアップが終わったので"
    elif [[ "$CMD" != run ]] && (( STARTED_HERE )); then
      reason="このコマンドのために起動したので"
    fi
    if [[ -n "$reason" ]]; then
      if [[ "$KEEP_RUNNING" == true ]]; then
        echo "KEEP_RUNNING=true のため VM は動いたままです。終わったら infra/gcp.sh stop で止めてください"
      else
        log "${reason} VM を自動で停止します (課金を止めるため)"
        gc compute instances stop "$VM_NAME" --zone "$ZONE" --quiet \
          || echo "VM の停止に失敗しました。infra/gcp.sh stop を実行してください" >&2
      fi
    fi
  elif (( rc != 0 )) && [[ -n "$st" ]]; then
    echo "VM は停止しています (状態: $st)。GPU の課金は止まっています"
    if [[ "$SPOT" == true ]] || recently_preempted; then
      if recently_preempted; then
        echo "原因: Spot VM が Google に回収されました (preempted)。このゾーンは今 L4 が混み合っています"
      fi
      echo "対策: 時間をおいて再実行するか、通常料金に切り替えます (infra/gcp.sh spot off、約 0.85 ドル/時間)"
    fi
  fi
  exit "$rc"
}

usage() { awk 'NR == 1 { next } /^#/ { sub(/^# ?/, ""); print; next } { exit }' "${BASH_SOURCE[0]}"; }

main() {
  local cmd="${1:-}"; shift || true
  CMD="$cmd"
  trap finish EXIT
  case "$cmd" in
    enable|quota|create|setup|run|status|fetch|ssh|stop|delete|spot) "cmd_$cmd" "$@" ;;
    *) usage; [[ -z "$cmd" ]] || exit 2 ;;
  esac
}

main "$@"
