"""要件テキストファイルを読んで全曲を連続生成する。

    .venv/bin/python make_music.py music_requirements.txt
    .venv/bin/python make_music.py music_requirements.txt --priority 1      # ① 必須 10 曲だけ
    .venv/bin/python make_music.py music_requirements.txt --only title kr   # 指定した상자だけ
    .venv/bin/python make_music.py music_requirements.txt --dry-run         # 生成せず一覧表示
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from musicgen_cpu.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main(["batch", *sys.argv[1:]]))
