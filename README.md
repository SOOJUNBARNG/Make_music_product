# Make_music_product

Meta の [MusicGen](https://huggingface.co/facebook/musicgen-medium) を **CPU だけで** 動かして、テキストから音楽を作るための基盤です。
GPU なしの Mac / PC で、要件テキストファイルに書いたゲーム BGM を一括生成できます。

## クイックスタート

```bash
source /path/to/your-venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
python make_music.py music_requirements.txt --priority 1
```

これで `music-source/` に必須 10 曲の WAV ができます。詳しくは下の各節を参照してください。

## 機能

- **CPU 推論**: `facebook/musicgen-small` を既定に、fp32・高性能コアのみで推論
- **30 秒を超える曲**: 直前の音を音声プロンプトにして継ぎ足し、1 分半〜3 分の曲も生成
- **ループ用の仕上げ**: 終わり→始まりのクロスフェード、ピーク正規化、曲ごとの音量 (`gain_db`)
- **要件ファイル駆動**: [music_requirements.txt](music_requirements.txt) を書き換えるだけで曲の追加・変更ができる
- **中断・再開**: 生成済みの曲はスキップ。書き込み途中のファイルは残らない
- **CLI / Python API**: `musicgen-cpu generate` で単発生成、`MusicGenerator` でスクリプトから利用

## モデル選定

| キー | リポジトリ | パラメータ | RAM 目安 (fp32) | CPU |
|---|---|---|---|---|
| **small** (既定) | `facebook/musicgen-small` | 300M | ~2GB | ◎ 推奨 |
| medium | `facebook/musicgen-medium` | 1.5B | ~7GB | △ 遅い・16GB RAM 推奨 |
| large | `facebook/musicgen-large` | 3.3B | ~14GB | × GPU 前提 |

CPU では **musicgen-small** を既定にしています。medium は small の約 5 倍のパラメータがあり、
8GB RAM のマシンではメモリが足りず、生成も数倍遅くなります。より高品質な音が必要で RAM に余裕があるときだけ `-m medium` を使ってください。

## セットアップ

Python 3.10 以上の仮想環境ならどれでも使えます (動作確認: Python 3.12 + torch 2.12 / transformers 4.56 と 5.20)。
既存の仮想環境を有効にして、必要なモジュールを入れてください。

```bash
source /path/to/your-venv/bin/activate
```

```bash
pip install -r requirements.txt
```

`make_music.py` はパッケージをインストールしなくても動きます。`musicgen-cpu` コマンドも使いたい場合だけ、追加で次を実行します。

```bash
pip install -e .
```

初回の生成時に Hugging Face からモデルが自動でダウンロードされます (small で約 2.4GB)。

## 使い方

```bash
musicgen-cpu generate "lo-fi hip hop beat with mellow piano and vinyl crackle" -d 10 --seed 42 -v
```

- プロンプトは **英語** で書くと精度が高くなります (学習データが英語のため)
- `-d` は秒数で、最大 30 秒です
- 出力は `outputs/` に 32kHz モノラルの WAV で保存されます
- 複数プロンプトを渡すことも、`-f prompts.txt` (1 行 1 プロンプト) で指定することもできます

```bash
musicgen-cpu models
```

主なオプション: `--guidance` (プロンプトへの忠実度、既定 3.0)、`--temperature`、`--top-k`、`--top-p`、`--batch-size`、`--threads`。

## 要件ファイルから全曲をまとめて作る

ゲーム用の 45 曲 (ゲーム側の音楽仕様 README_music.md にある「상자」) の要件を [music_requirements.txt](music_requirements.txt) にまとめています。
このファイルを読んで、上から順に全曲を生成します。

```bash
python make_music.py music_requirements.txt
```

- 出力先は `music-source/<상자>.wav` で、そのまま `tools/add-music.sh` に渡せます
- **生成済みの曲はスキップ**するので、途中で止めても同じコマンドで続きから再開できます (`--overwrite` で作り直し)
- 30 秒を超える曲は、直前 10 秒を音声プロンプトにして 30 秒ずつ継ぎ足して作ります
- 終わりと始まりを 2 秒クロスフェードして、ループ再生で途切れないようにしています
- `gain_db` で会話シーン用の曲を小さめにしています

よく使うオプション:

```bash
python make_music.py music_requirements.txt --priority 1
```

```bash
python make_music.py music_requirements.txt --only title kr
```

```bash
python make_music.py music_requirements.txt --dry-run
```

`--priority 1` は ① 必須 10 曲だけ、`--only` は指定した상자だけ、`--dry-run` は生成せずに一覧とプロンプトを表示します。

要件の書き方 (INI 形式):

```ini
[trial.storm]          # 상자 이름 = 出力ファイル名
priority = 2           # ①=1 / ②=2 / ③=3
duration = 45          # 秒
prompt = violent sea storm, pounding taiko drums, ...   # 英語で
gain_db = -6           # 任意: 音量
copy_of = scene.opening  # 任意: 生成せず別の曲をコピー
```

`[settings]` でモデル、出力先、シード、全曲共通のスタイル (`style`) を変えられます。

### 所要時間の目安

全 45 曲で合計約 38 分ぶんの音楽です。CPU の musicgen-small では、生成に音楽の長さの数倍から十数倍の時間がかかります。
全曲生成は数時間かかる前提で、寝ている間などに流しっぱなしにしてください。まず `--priority 1` から始めるのがおすすめです。
**RAM の空きが少ないとスワップで極端に遅くなる**ので、ブラウザなど他のアプリはなるべく閉じてから実行してください。

## Python から使う

```python
from musicgen_cpu import GenerationConfig, MusicGenerator, save_wav

gen = MusicGenerator("small")
[result] = gen.generate("epic orchestral trailer music", GenerationConfig(duration=10, seed=0))
save_wav("trailer.wav", result.audio, result.sample_rate)
```

## 構成

```
make_music.py            要件ファイルを読んで全曲を生成するエントリポイント
music_requirements.txt   45 曲ぶんの要件 (プロンプト・長さ・優先度・音量)
src/musicgen_cpu/
  config.py      モデル定義 (ModelSpec) と生成パラメータ (GenerationConfig)
  generator.py   MusicGenerator: モデルの遅延ロード、CPU 推論、長尺の継ぎ足し生成
  batch.py       要件ファイルの読み込みと連続生成 (スキップ・再開・コピー)
  postprocess.py ループ用クロスフェードと音量調整
  audio.py       WAV 書き出し (標準ライブラリの wave を使用)
  cli.py         musicgen-cpu コマンド (models / generate / batch)
tests/           モデル不要のユニットテスト
```

## トラブルシューティング

- **極端に遅い / 進まない**: ほとんどの場合メモリ不足によるスワップです。アクティビティモニタの「メモリプレッシャー」が黄〜赤なら、
  他のアプリを閉じるか再起動してから実行してください。8GB RAM の Mac では空きメモリ 3GB 以上が目安です
- **初回が遅い**: モデル (約 2.4GB) のダウンロードが入ります。2 回目以降は `~/.cache/huggingface` のキャッシュを使います
- **途中で止めたい**: Ctrl+C で止めて大丈夫です。同じコマンドを再実行すると、完成していない曲から再開します
- **音のイメージが違う**: `music_requirements.txt` の `prompt` を英語で具体的に書き直し、`--only <상자> --overwrite` で作り直します。
  `seed` を変えると同じプロンプトでも別の曲になります

## テスト

```bash
PYTHONPATH=src python -m pytest
```
