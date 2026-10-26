# Make_music_product

テキストからゲーム BGM を生成するプロジェクトです。
Google Cloud の L4 GPU で [ACE-Step 1.5](https://github.com/ACE-Step/ACE-Step-1.5) を動かし、
要件テキストファイル [music_requirements.txt](music_requirements.txt) に書いた 45 曲をまとめて生成します。

- **モデル**: ACE-Step 1.5 XL turbo (DiT 4B) + 5Hz LM 1.7B。MIT ライセンスで商用利用可。1 回で最大 10 分まで作れる
- **GPU**: GCP プロジェクト `jpix-it` の `g2-standard-8` (NVIDIA L4 24GB)。既定は Spot
- **出力**: `music-source/<상자>.wav` (48kHz ステレオ・16bit)。ループ用に終わりと始まりをクロスフェード済み
- 計画と選定理由: [docs/gpu-plan.md](docs/gpu-plan.md)
- CPU で MusicGen small を動かす旧構成: [OLD/](OLD/)

## 手順

手元の Mac で `gcloud` にログインしてある前提です。設定は [infra/gcp.env](infra/gcp.env) で変えられます
(リージョン、Spot か通常料金か、VM 名など)。gcloud の既定プロジェクトは変えず、毎回 `--project jpix-it` を付けて実行します。

**1. Compute Engine API を有効化** (無料)

```bash
infra/gcp.sh enable
```

**2. L4 GPU の割り当てを確認**

```bash
infra/gcp.sh quota
```

足りない場合は、表示されるリンクから割り当ての増加を申請します (承認まで数分〜数日)。

**3. VM を作成** (ここから課金が始まります)

```bash
infra/gcp.sh create
```

**4. ACE-Step 1.5 とモデルを VM に入れる** (初回のみ。10〜20 分ほど)

```bash
infra/gcp.sh setup
```

**5. 生成を開始**

```bash
infra/gcp.sh run --priority 1
```

引数はそのまま `make_music.py` に渡ります。`--priority 1` は ① 必須 10 曲だけで、引数なしなら全 45 曲です。
生成が終わると VM は自動で停止します。

**6. 進み具合の確認と回収**

```bash
infra/gcp.sh status
```

```bash
infra/gcp.sh fetch
```

`fetch` で `music-source/` に WAV がコピーされます。止まっている VM は自動で起動するので、回収したら `infra/gcp.sh stop` で止めてください。

**7. 使い終わったら削除** (停止中もディスク代がかかるため)

```bash
infra/gcp.sh delete
```

### Spot で途中で止められたら

Spot VM は Google の都合で停止されることがあります。生成済みの曲は残っているので、もう一度 `infra/gcp.sh run` を実行すれば続きから再開します。

## 要件ファイル

[music_requirements.txt](music_requirements.txt) に 1 曲 1 セクションで書きます。

```ini
[trial.storm]          # 상자 이름 = 出力ファイル名
priority = 2           # ①=1 / ②=2 / ③=3
duration = 45          # 秒 (10〜598)
prompt = violent sea storm, pounding taiko drums, ...   # 英語で
gain_db = -6           # 任意: 音量
bpm = 120              # 任意: テンポ・調・拍子 (省略すると ACE-Step が決める)
copy_of = scene.opening  # 任意: 生成せず別の曲をコピー
```

`[settings]` で出力先、シード、全曲共通のスタイル、ACE-Step のモデル (`dit_model` / `lm_model`) を変えられます。
品質を上げたいときは `dit_model = acestep-v15-xl-sft` と `inference_steps = 50` にします (遅くなります)。

VM を使わずに、対象の曲とプロンプトの一覧だけ確認できます。

```bash
python make_music.py music_requirements.txt --dry-run
```

## 構成

```
infra/gcp.sh            GCP の操作 (enable / quota / create / setup / run / status / fetch / stop / delete)
infra/gcp.env           GCP の設定 (プロジェクト・ゾーン・マシン・Spot など)
make_music.py           VM 上で全曲を生成するエントリポイント
music_requirements.txt  45 曲ぶんの要件
src/makemusic/
  requirements.py   要件ファイルの読み込みと検証
  runner.py         連続生成 (スキップ・再開・コピー・失敗しても続行)
  acestep_backend.py ACE-Step 1.5 の呼び出し
  audio.py          ループ用クロスフェード・音量調整・WAV 書き出し
tests/              GPU 不要のテスト
OLD/                旧構成 (CPU / MusicGen small)
```

## テスト

GPU も ACE-Step も無しで動きます (ACE-Step の API は偽のモジュールで代用)。

```bash
python -m pytest tests
```
