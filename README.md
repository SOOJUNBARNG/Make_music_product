# Make_music_product

テキストから音楽 (ゲーム BGM) を生成するプロジェクトです。

## 現在の状況

- **GPU 版を準備中**: Google Cloud の L4 GPU で ACE-Step を使って生成する構成に移行します。計画は [docs/gpu-plan.md](docs/gpu-plan.md) にあります
- **CPU 版 (旧構成)**: MusicGen small を CPU で動かす旧構成は [OLD/](OLD/) にそのまま残しています。使い方は [OLD/README.md](OLD/README.md) を参照してください

```bash
cd OLD && python make_music.py music_requirements.txt --dry-run
```
