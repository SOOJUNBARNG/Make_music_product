#!/usr/bin/env bash
# GCP の L4 GPU VM で ACE-Step 1.5 を動かし、要件ファイルの全曲を生成する。
#
#   infra/gcp.sh enable      Compute Engine API を有効化
#   infra/gcp.sh quota       L4 GPU の割り当てを確認
#   infra/gcp.sh create      VM を作成
#   infra/gcp.sh setup       VM に ACE-Step 1.5 とモデルを入れる (初回のみ・再実行しても安全)
#   infra/gcp.sh run [引数]  コードと要件ファイルを送って生成開始 (例: run --priority 1)
#   infra/gcp.sh status      VM の状態と生成ログの末尾を表示
#   infra/gcp.sh fetch       生成した WAV を手元の music-source/ にコピー
#   infra/gcp.sh ssh         VM にログイン
#   infra/gcp.sh stop        VM を停止 (ディスク代だけかかる)
#   infra/gcp.sh delete      VM をディスクごと削除 (課金が完全に止まる)
#
# 設定は infra/gcp.env。gcloud の既定プロジェクトは変更せず、毎回 --project を付ける。
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"

# 環境変数で渡した値を gcp.env より優先する
_overrides="$(env | grep -E '^(PROJECT|ZONE|VM_NAME|MACHINE_TYPE|SPOT|DISK_SIZE_GB|IMAGE_FAMILY|IMAGE_PROJECT|ACESTEP_REPO|AUTO_SHUTDOWN)=' || true)"
# shellcheck source=gcp.env
source "$HERE/gcp.env"
while IFS= read -r kv; do [[ -n "$kv" ]] && export "${kv?}"; done <<< "$_overrides"

REGION="${ZONE%-*}"
REMOTE_DIR="makemusic"           # VM のホーム直下
ACESTEP_DIR="ACE-Step-1.5"

gc() { gcloud --project "$PROJECT" "$@"; }
remote() { gc compute ssh "$VM_NAME" --zone "$ZONE" --quiet --command "$1"; }
log() { printf '\033[1m==> %s\033[0m\n' "$*"; }
die() { printf 'エラー: %s\n' "$*" >&2; exit 1; }

vm_status() { gc compute instances describe "$VM_NAME" --zone "$ZONE" --format='value(status)' 2>/dev/null || true; }

ensure_running() {
  local st; st="$(vm_status)"
  [[ -n "$st" ]] || die "VM $VM_NAME がありません。先に infra/gcp.sh create を実行してください"
  if [[ "$st" != "RUNNING" ]]; then
    log "VM を起動します ($st → RUNNING)"
    gc compute instances start "$VM_NAME" --zone "$ZONE"
  fi
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
  if (( all_limit - all_usage < 1 )); then ok=0; echo "→ GPUS_ALL_REGIONS が足りません"; fi
  if (( l4_limit - l4_usage < 1 )); then ok=0; echo "→ $l4_metric ($REGION) が足りません"; fi
  if (( ok )); then
    echo "OK: L4 を 1 枚使えます"
  else
    cat <<EOF

割り当ての増加を申請してください (承認まで数分〜数日):
  https://console.cloud.google.com/iam-admin/quotas?project=$PROJECT
  上の画面で「GPUS_ALL_REGIONS」と「${l4_metric}」(リージョン ${REGION}) をそれぞれ 1 以上に。
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
  [[ -z "$(vm_status)" ]] || die "VM $VM_NAME はすでにあります (状態: $(vm_status))"
  local family; family="$(pick_image_family)"
  local spot_args=()
  [[ "$SPOT" == true ]] && spot_args=(--provisioning-model=SPOT --instance-termination-action=STOP)
  log "VM を作成: $VM_NAME ($MACHINE_TYPE, $ZONE, spot=$SPOT, image=$family)"
  gc compute instances create "$VM_NAME" \
    --zone "$ZONE" \
    --machine-type "$MACHINE_TYPE" \
    --maintenance-policy TERMINATE \
    ${spot_args[@]+"${spot_args[@]}"} \
    --image-family "$family" --image-project "$IMAGE_PROJECT" \
    --boot-disk-size "${DISK_SIZE_GB}GB" --boot-disk-type pd-balanced \
    --metadata install-nvidia-driver=True \
    --scopes cloud-platform
  echo "作成しました。ドライバのインストールに数分かかるので、少し待ってから infra/gcp.sh setup を実行してください"
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
  ls "$ROOT/music-source" | grep -c '\.wav$' | sed 's/^/手元の曲数: /'
}

cmd_ssh() { ensure_running; gc compute ssh "$VM_NAME" --zone "$ZONE"; }
cmd_stop() { log "VM を停止"; gc compute instances stop "$VM_NAME" --zone "$ZONE"; }
cmd_delete() {
  read -r -p "VM $VM_NAME をディスクごと削除します。生成した曲は fetch 済みですか? [y/N] " yn
  [[ "$yn" == [yY] ]] || { echo 中止しました; return 1; }
  gc compute instances delete "$VM_NAME" --zone "$ZONE" --quiet
}

usage() { sed -n '2,15p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

main() {
  local cmd="${1:-}"; shift || true
  case "$cmd" in
    enable|quota|create|setup|run|status|fetch|ssh|stop|delete) "cmd_$cmd" "$@" ;;
    *) usage; [[ -z "$cmd" ]] || exit 2 ;;
  esac
}

main "$@"
