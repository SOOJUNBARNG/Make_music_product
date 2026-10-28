# Make_music_product

テキストからゲーム BGM を作るプロジェクトです。
Google Cloud の L4 GPU で [ACE-Step 1.5](https://github.com/ACE-Step/ACE-Step-1.5) を動かし、
要件テキストファイル [music_requirements.txt](music_requirements.txt) に書いた **56 曲 (合計約 52 分)** をまとめて生成します。

曲の要件は、ゲーム側の音楽仕様 `docs/music-brief.md` (2026-10-27、第1部 45 상자 + 第2部 11 상자) に合わせています。

## 現在の状況 (2026-10-28)

| 段階 | 状態 |
|---|---|
| コード (生成スクリプト・GCP 操作スクリプト・要件ファイル) | ✅ 実装済み。テストは GPU なしで通過 |
| Compute Engine API の有効化 | ✅ 完了 |
| GPU の割り当て (`GPUS_ALL_REGIONS`・Spot L4) | ✅ どちらも 1 で承認済み |
| VM の作成 | ✅ `makemusic-l4` (us-central1-a)。一度は品切れで失敗したため、b・c も自動で試すように修正済み |
| ACE-Step のセットアップ (`setup`) | ✅ 完了 (`SETUP_OK`)。GPU は NVIDIA L4 (23,034 MiB)、ACE-Step 1.5.0、torch 2.10 + CUDA 12.8 |
| 生成 (`run`) | ⚠️ 未実施。us-central1-a の Spot VM が起動後 1〜17 分で 3 回回収 (preempted) され、その後は品切れで起動もできない。通常料金は使わず Spot のまま、空きのあるゾーン (GCP によると us-central1-c) へ `infra/gcp.sh move` で移すか、時間をおいて再試行する方針 |

## 概要

| 項目 | 内容 |
|---|---|
| モデル | ACE-Step 1.5 **XL turbo** (DiT 4B, 8 ステップ) + **5Hz LM 1.7B**。MIT ライセンスで商用利用可。1 回の生成で 10 秒〜10 分 |
| GPU | GCP プロジェクト `jpix-it` の `g2-standard-8` (8 vCPU / 32GB / NVIDIA L4 24GB)。既定は **Spot** |
| 出力 | `music-source/<상자>.wav` (48kHz ステレオ・16bit)。ゲームの `tools/add-music.sh` にそのまま渡せる |
| 仕上げ | 終わり→始まりを 2 秒クロスフェードしてループ再生で途切れないように加工。ピーク -1dBFS に正規化 |
| 計画と選定理由 | [docs/gpu-plan.md](docs/gpu-plan.md) |
| 旧構成 | CPU で MusicGen small を動かす版は [OLD/](OLD/) (MusicGen の重みは非商用ライセンスのため、ゲームには使わない) |

### しくみ

```
手元の Mac                                     GCP (jpix-it, us-central1)
─────────────────────────                      ──────────────────────────────────────
music_requirements.txt ─┐                      VM: makemusic-l4 (g2-standard-8, L4)
src/ make_music.py ─────┼── infra/gcp.sh run ──▶  ~/makemusic/        ← コードと要件ファイル
                        │                         ~/ACE-Step-1.5/     ← ACE-Step 本体とモデル
                        │                              │
                        │                              ▼ 1 曲ずつ生成 → ループ加工 → WAV
music-source/*.wav ◀────┴── infra/gcp.sh fetch ── ~/makemusic/music-source/*.wav
                                                       │
                                                  生成が終わると VM は自動で停止
```

## 費用の目安

ACE-Step を GPU で実際に動かした実測はまだないので、**すべて概算** です。料金は変わることがあるので、最新の金額は
[GCP の料金ページ](https://cloud.google.com/products/compute/pricing/accelerator-optimized) で確認してください。

### 単価 (us-central1、GPU 込み)

| 項目 | 単価 |
|---|---|
| `g2-standard-8` 通常料金 | 約 **0.85 ドル / 時間** |
| `g2-standard-8` Spot | 約 **0.2〜0.7 ドル / 時間** (時期によって変わる) |
| ディスク 100GB (pd-balanced) | 約 **10 ドル / 月** (VM を止めていてもかかる。削除すれば止まる) |
| 生成した WAV のダウンロード | 全 56 曲で約 0.6GB → 0.1 ドル未満 |

### 1 回ぶんの作業時間と費用

| 作業 | VM が動く時間 (見込み) |
|---|---|
| `setup` (ACE-Step とモデルのインストール) | 約 10 分 (初回のみ。実測 7 分) |
| 全 56 曲の生成 | 1〜2 時間 (1 曲 30 秒〜2 分の見込み) |
| `fetch` と確認 | 10 分ほど |
| **合計** | **約 2〜3 時間** |

| ケース | Spot | 通常料金 |
|---|---|---|
| 全 56 曲を 1 回作る (VM 3 時間) | 約 0.5〜2 ドル | 約 2.5 ドル |
| プロンプトを直して何度か作り直す (VM 合計 8 時間) | 約 2〜6 ドル | 約 7 ドル |
| ディスク (1 週間で削除 / 1 か月残す) | 約 2.5 / 10 ドル | 約 2.5 / 10 ドル |
| **合計の目安** | **約 3〜15 ドル** | **約 5〜17 ドル** |

日本円・韓国ウォンでは、だいたい **数百円〜2,000 円台 (数千〜2 万ウォン台)** の見込みです。

### 注意

- **VM の止め忘れがいちばん高くつきます** (通常料金で丸 1 日動かすと約 20 ドル)。そのため `infra/gcp.sh` は次のときに **VM を自動で停止** します
  - `setup`・`run`・`fetch`・`ssh` が失敗したとき (ただし、もともと動いていた VM は生成中かもしれないので `fetch`・`ssh` の失敗では止めない)
  - `setup` が終わったとき
  - `fetch`・`ssh` のために VM を起動した場合、そのコマンドが終わったとき
  - `run` で始めた生成が終わったとき (VM 自身が停止する)
- 自動停止させたくないときは `KEEP_RUNNING=true infra/gcp.sh setup` のように付けます
- **使い終わったら `infra/gcp.sh delete`**: 停止中でもディスク代 (月 10 ドル前後) がかかり続けます
- **予算アラートの設定をおすすめします**: [請求先アカウントの予算とアラート](https://console.cloud.google.com/billing/budgets) で、例えば 20 ドルを超えたらメールが届くようにしておくと安心です

## 前提

- 手元の Mac に [Google Cloud CLI](https://cloud.google.com/sdk/docs/install) (`gcloud`) が入っていて、`jpix-it` の Owner 権限のアカウント (`powwerer@gmail.com`) でログイン済み
- gcloud の既定プロジェクトは別のプロジェクトのままで構いません。`infra/gcp.sh` は毎回 `--project jpix-it` を付けて実行します
- 生成したい曲を [music_requirements.txt](music_requirements.txt) に書いてある (56 曲ぶんは記入済み)

コマンドはすべてリポジトリのルート (`/Users/barng/Make_music_product`) で実行します。

## 手順

### 1. Compute Engine API を有効化 (完了済み・無料)

```bash
infra/gcp.sh enable
```

### 2. GPU の割り当てを確認 (完了済み)

```bash
infra/gcp.sh quota
```

「OK: L4 を 1 枚使えます」と出れば準備完了です。足りない割り当てがあると、その名前と申請ページのリンクが表示されます。

申請するときは、[割り当てのページ](https://console.cloud.google.com/iam-admin/quotas?project=jpix-it) で次の手順を踏みます。

1. 表示された割り当て名 (例: `GPUs (all regions)`) でフィルタします
2. 行にチェックを入れて「割り当てを編集」を押します
3. 新しい上限を `1` にし、用途を英語で書いて送信します

承認は数分〜数日で、結果はメールで届きます。

### 3. VM を作成 (ここから課金が始まります)

```bash
infra/gcp.sh create
```

- Spot の L4 は、ゾーンによって品切れのことがあります (`ZONE_RESOURCE_POOL_EXHAUSTED`)。`create` は **us-central1-a → b → c の順に自動で試し**、品切れのゾーンは飛ばします
- 作れたゾーンは `infra/.vm-zone` に記録され、以降のコマンドは自動でそのゾーンを使います
- 3 ゾーンとも品切れのときは、数十分〜数時間おいてから再実行してください
- 成功すると「作成しました (ゾーン: …)」と表示されます

### 4. ACE-Step 1.5 とモデルを VM に入れる (初回のみ、約 10 分)

VM 作成後、GPU ドライバのインストールに数分かかります。`setup` はドライバの準備ができるまで自動で待ってから始まります。

```bash
infra/gcp.sh setup
```

やること:
1. GPU を確認します (`nvidia-smi` で L4 と 24GB が表示されます)
2. Python のパッケージ管理ツール [uv](https://docs.astral.sh/uv/) を入れます
3. ACE-Step-1.5 を `~/ACE-Step-1.5` に clone して `uv sync` します
4. モデル (標準セットと XL turbo) をダウンロードします

最後に `SETUP_OK` と出れば成功です。再実行しても安全なので、途中で失敗したらもう一度実行できます。

- 初回は gcloud が SSH 鍵を作り、`Connection refused` が数回出ることがあります。VM の起動待ちなので、そのまま待てば大丈夫です
- L4 は `nvidia-smi` で約 23,000 MiB と表示されます。ACE-Step の公式ガイドでは「20〜24GB」の区分で、推奨構成は XL + LM 1.7B (このリポジトリの既定値) です

`setup` が終わると VM は自動で停止します。

### 5. 生成を開始

最初は 1 曲だけ作って、ACE-Step が正しく動くか確認するのがおすすめです (`goal` は 30 秒の曲)。

```bash
infra/gcp.sh run --only goal
```

問題なければ、必須の 12 曲を作ります。

```bash
infra/gcp.sh run --priority 1
```

全 56 曲を作るときは引数なしで実行します。

```bash
infra/gcp.sh run
```

- コード・要件ファイルを VM に送り、バックグラウンドで生成を始めます。手元のターミナルを閉じても生成は続きます
- 生成済みの曲はスキップするので、`--priority 1` のあとに引数なしで実行すると、残りの 44 曲だけを作ります
- 生成が終わると **VM は自動で停止** します (`infra/gcp.env` の `AUTO_SHUTDOWN=true`)
- 引数はそのまま `make_music.py` に渡ります (下の「make_music.py の引数」を参照)

### 6. 進み具合を確認

```bash
infra/gcp.sh status
```

VM の状態、生成ログの最後の 20 行、完成した曲数が表示されます。ログの例:

```
[3/12] jp: 120s 生成中...
[3/12] jp: 完了 jp.wav (120s audio, 48s)
```

VM が `TERMINATED` (停止) と表示されたら、生成が終わったか、Spot で止められたかのどちらかです。

### 7. 生成した曲を手元にコピー

```bash
infra/gcp.sh fetch
```

`music-source/` に WAV がコピーされます。止まっている VM は自動で起動し、コピーが終わると自動で停止します。

コピーした WAV は、ゲーム側の `music-source/` に入れて `tools/add-music.sh` を実行すれば、ゲームに組み込まれます。

### 8. 使い終わったら VM を削除

停止中もディスク代がかかるので、作り直す予定がなくなったら削除します。確認のプロンプトが出ます。

```bash
infra/gcp.sh delete
```

ACE-Step のモデルも一緒に消えるので、また使うときは `create` と `setup` からやり直しです。

## 曲を作り直すとき

1. [music_requirements.txt](music_requirements.txt) の該当する상자の `prompt` を書き直します。`seed` を変えるだけでも、同じプロンプトで別の曲になります
2. その曲だけ作り直します (`--overwrite` で既存のファイルを上書き)

```bash
infra/gcp.sh run --only kr jp --overwrite
```

3. `status` で終わったのを確認してから `fetch` します

## コマンド一覧

### infra/gcp.sh

| コマンド | 内容 | 課金 |
|---|---|---|
| `enable` | Compute Engine API を有効化 | なし |
| `quota` | L4 GPU の割り当てを確認 | なし |
| `create` | VM を作成 (品切れのゾーンは飛ばす) | ここから開始 |
| `setup` | ACE-Step 1.5 とモデルを VM に入れる | VM が動く |
| `run [引数]` | コードと要件ファイルを送って生成開始。終わると自動停止 | VM が動く |
| `status` | VM の状態と生成ログの末尾を表示 | なし |
| `fetch` | 生成した WAV を手元の `music-source/` にコピー (止まっていれば起動) | VM が動く |
| `ssh` | VM にログイン | VM が動く |
| `stop` | VM を停止 | ディスク代だけ |
| `delete` | VM をディスクごと削除 | 止まる |
| `spot on` / `spot off` | 既存の VM を Spot / 通常料金に切り替える (動いていれば先に停止する) | なし |
| `move ゾーン` | VM を同じリージョンの別ゾーンに作り直し、続けて `setup` して停止する (品切れ対策。確認あり) | VM が動く (約 10 分) |

### make_music.py の引数

`infra/gcp.sh run` に付けた引数は、そのまま VM 上の `make_music.py` に渡ります。

| 引数 | 内容 |
|---|---|
| `--priority 1` | 優先度 1 (꼭 필요한 곡、12 曲) だけ。`2` なら優先度 1〜2 |
| `--only 상자 …` | 指定した상자だけ (例: `--only title kr`) |
| `--overwrite` | 既存の WAV も作り直す |
| `--dry-run` | 生成せず、対象の曲とプロンプトの一覧を表示 |
| `-o 出力先` | 要件ファイルの `output_dir` を上書き |

手元で一覧だけ確認したいときは、GPU なしで実行できます (Python 3.10 以上と numpy が必要)。

```bash
python make_music.py music_requirements.txt --dry-run
```

## 設定

### infra/gcp.env (GCP の設定)

環境変数で一時的に上書きもできます (例: `SPOT=false infra/gcp.sh create`)。

| 設定 | 既定値 | 内容 |
|---|---|---|
| `PROJECT` | `jpix-it` | GCP プロジェクト |
| `ZONE` | `us-central1-a` | 第一候補のゾーン。環境変数で指定するとそのゾーンだけを試す |
| `ZONE_CANDIDATES` | `us-central1-a us-central1-b us-central1-c` | `create` が順に試すゾーン。割り当てがリージョン単位なので同じリージョン内で並べる |
| `VM_NAME` | `makemusic-l4` | VM の名前 |
| `MACHINE_TYPE` | `g2-standard-8` | 8 vCPU / 32GB / L4 ×1 |
| `SPOT` | `true` | `false` で通常料金 (空きは見つかりやすいが数倍高い) |
| `DISK_SIZE_GB` | `100` | ディスク容量 |
| `IMAGE_FAMILY` | (空) | 空なら CUDA 入りの Deep Learning VM (Ubuntu 22.04) の最新を自動で選ぶ |
| `AUTO_SHUTDOWN` | `true` | 生成が終わったら VM を停止する |
| `KEEP_RUNNING` | `false` | `true` にすると、失敗時・`setup` 後などの自動停止をしない |

### music_requirements.txt の [settings] (全曲共通)

| 設定 | 既定値 | 内容 |
|---|---|---|
| `output_dir` | `music-source` | 出力先 (要件ファイルの場所が基準) |
| `seed` | `1234` | 乱数シードの基準。曲ごとに「基準 + 要件ファイル内の順番」になる |
| `default_duration` | `45` | `duration` を書かなかった曲の長さ (秒) |
| `loop_crossfade` | `2.0` | ループ用のクロスフェード秒数。この分だけ長く生成してから切り落とす |
| `style` | music-brief.md の共通文 + `soft gentle intro` | 全プロンプトの末尾に付ける共通スタイル |
| `dit_model` | `acestep-v15-xl-turbo` | 品質優先なら `acestep-v15-xl-sft` (`inference_steps = 50` にする。生成は数倍遅くなる) |
| `lm_model` | `acestep-5Hz-lm-1.7B` | 軽くしたいときは `acestep-5Hz-lm-0.6B` |
| `lm_backend` | `vllm` | うまく動かないときは `pt` |
| `inference_steps` | `8` | turbo は 8、sft/base は 32〜64 |
| `shift` | `3.0` | turbo 向けの推奨値 |
| `thinking` | `true` | LM が曲の構成 (BPM・調など) を考えてから生成する |

### music_requirements.txt の曲ごとの設定

```ini
[trial.storm]          # 상자 이름 = 出力ファイル名 (trial.storm.wav)
priority = 2           # 1: 꼭 필요한 곡 / 2: 있으면 좋은 곡 / 3: 나머지
duration = 45          # 秒。duration + loop_crossfade が 10〜600 秒になるように
prompt = Violent sea storm, rolling taiko and low strings,
    crashing waves and wind, dramatic but not a battle
gain_db = -6           # 任意: 音量 (dB)
seed = 42              # 任意: この曲だけシードを固定
bpm = 120              # 任意: テンポ (30〜300)
keyscale = D minor     # 任意: 調
timesignature = 4      # 任意: 拍子 (2 / 3 / 4 / 6)
copy_of = scene.opening  # 任意: 生成せず別の曲をコピー (prompt などは不要)
```

- `prompt` は英語で書きます。次の行をインデントすると複数行で書けます。`style` と合わせて 512 文字以内です
- `bpm`・`keyscale`・`timesignature` を省略すると、ACE-Step の LM が決めます
- 未知のキー (書き間違い) や範囲外の値があると、生成を始める前にエラーで止まります

### 要件の決め方 (music-brief.md との対応)

| 項目 | 内容 |
|---|---|
| 상자 | music-brief.md「3. 상자 목록」の 56 個すべて |
| 優先度 | 「꼭 필요한」= 1 (第1部 10 + 第2部 2)、「있으면 좋은」= 2、それ以外 = 3 |
| プロンプト | 「7. AI 음악 도구용 프롬프트」にある 24 상자はそのまま使用。残り 32 상자は「3.」の場面説明から作成 |
| 共通スタイル | 「7.」の共通文に、「4.」の「처음 몇 초에 큰 소리가 나지 않게」に合わせて `soft gentle intro` を追加 |
| 長さ | 「4. 파일 규격」どおり、地域の曲 (기본 음악) 120 秒、場面・試練の曲 45〜60 秒、目標達成 20〜30 秒 |
| 音量 | 会話シーン (`scene.*`) の曲は、台詞を邪魔しないよう全部 -6dB |
| 同じ曲 | `scene.openingJp`・`scene.openingIn`・`scene.meetIn` は対になる曲をコピー |

## うまくいかないとき

| 症状 | 原因と対処 |
|---|---|
| `create` で `ZONE_RESOURCE_POOL_EXHAUSTED` | そのゾーンで L4 が品切れ。自動で次のゾーンを試します。全部だめなら時間をおいて再実行するか、`SPOT=false` で通常料金にする |
| `quota` で「足りません」 | 表示された割り当ての増加を申請する (「手順 2」を参照) |
| `VM makemusic-l4 がありません` | まだ作成していないか、別のゾーンにある。`infra/.vm-zone` のゾーンを確認する |
| 初回の `ssh`・`setup` で SSH 鍵の作成メッセージが出る | 初回だけ gcloud が鍵を作ります。そのまま進めて大丈夫 |
| `Connection refused`・`Operation timed out` で止まる | VM の起動直後で SSH がまだ準備できていないか、Spot で回収された。SSH は自動で最大 5 分待ち、VM が止まったら原因を表示する。失敗したときは VM も自動で止まる |
| `setup` が「GPU ドライバの準備を待っています」のまま進まない | 10 分待っても進まなければ `infra/gcp.sh ssh` でログインし、`nvidia-smi` を実行して表示を確認する |
| `setup` の `uv sync` やダウンロードで失敗 | ネットワークの一時的なエラーのことが多い。もう一度 `setup` を実行する |
| 生成が `vllm` 関係のエラーで止まる | `music_requirements.txt` の `lm_backend = pt` に変えて `run` し直す |
| `status` で VM が `TERMINATED` なのに曲が足りない | Spot で止められた。`run` をもう一度実行すれば続きから再開する |
| 「〜には今 L4 の空きがありません (VM を起動できませんでした)」と出る | VM のあるゾーンで L4 が品切れ。GCP が空きのあるゾーンを教えてくれた場合は、表示された `infra/gcp.sh move <ゾーン>` で作り直す (ACE-Step とモデルは自動で入れ直す)。教えてくれなかった場合は時間をおいて再実行する |
| 「Spot VM が Google に回収されました (preempted)」と出る | そのゾーンの L4 が混み合っていて、Spot VM がすぐ止められている。時間をおいて再実行するか、`infra/gcp.sh spot off` で通常料金 (約 0.85 ドル/時間) に切り替える。`infra/gcp.env` の `SPOT=false` も合わせて変えておく |
| 特定の曲だけ失敗した | ログの最後に「失敗した상자」が出る。`run --only <상자>` で作り直す |
| 音のイメージが違う | `prompt` を具体的に書き直すか `seed` を変えて、`run --only <상자> --overwrite` |

## ファイル構成

```
infra/gcp.sh             GCP の操作 (enable / quota / create / setup / run / status / fetch / ssh / stop / delete)
infra/gcp.env            GCP の設定 (プロジェクト・ゾーン・マシン・Spot など)
infra/.vm-zone           VM を作れたゾーンの記録 (create が書く。Git 管理外)
make_music.py            VM 上で全曲を生成するエントリポイント
music_requirements.txt   56 曲ぶんの要件 (music-brief.md のプロンプトを使用)
src/makemusic/
  requirements.py        要件ファイルの読み込みと検証 (長さ・文字数・未知のキー)
  runner.py              連続生成 (スキップ・再開・コピー・1 曲失敗しても続行・書きかけファイルを残さない)
  acestep_backend.py     ACE-Step 1.5 の呼び出し (モデルは最初の 1 回だけ読み込む)
  audio.py               ループ用クロスフェード・音量調整・WAV 書き出し
tests/                   GPU 不要のテスト
docs/gpu-plan.md         GPU 版の計画と、モデル・GPU の選定理由
OLD/                     旧構成 (CPU / MusicGen small)
music-source/            生成した WAV の置き場 (Git 管理外)
```

## 権利について

- **ACE-Step 1.5** は MIT ライセンスで、生成した音楽の商用利用 (ゲームへの組み込み) ができます
- music-brief.md「5.」にあるとおり、公開前に AI ツールの利用規約をもう一度確認してください。民謡の旋律を使う場合も、他人の編曲や録音に似ていないかに注意します
- 旧構成の MusicGen (`OLD/`) は重みが **CC-BY-NC 4.0 (非商用のみ)** なので、そちらで作った曲はゲームに使わないでください

## テスト

GPU も ACE-Step もなしで動きます。ACE-Step の API は、公式ドキュメントの形に合わせた偽のモジュールで代用しています。

```bash
python -m pytest tests
```

確認している内容:
- 要件ファイルの読み込みと、範囲外の値・書き間違いのエラー
- 同梱の要件ファイルが music-brief.md の規格 (曲数・長さ・音量) を満たしていること
- 生成・スキップ・再開・コピー・失敗時の続行
- ループ加工、WAV 書き出し
- ACE-Step を、公式ドキュメントどおりの引数で呼んでいること
