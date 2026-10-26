"""要件テキストファイルを読んで全曲を ACE-Step 1.5 で連続生成する (GPU の VM 上で実行)。

    python make_music.py music_requirements.txt
    python make_music.py music_requirements.txt --priority 1      # ① 必須 10 曲だけ
    python make_music.py music_requirements.txt --only title kr   # 指定した상자だけ
    python make_music.py music_requirements.txt --dry-run         # 生成せず一覧表示 (GPU 不要)

ふつうは手元から infra/gcp.sh run を使えば、VM 上でこのスクリプトが動きます。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

from makemusic.runner import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
