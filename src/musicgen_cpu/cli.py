"""コマンドライン: `musicgen-cpu generate "lofi piano" -d 10`"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from datetime import datetime
from pathlib import Path

from .audio import save_wav
from .config import DEFAULT_MODEL, MAX_DURATION_SEC, MODELS, GenerationConfig


def slugify(text: str, max_len: int = 40) -> str:
    slug = re.sub(r"[^A-Za-z0-9]+", "-", text).strip("-").lower()
    return slug[:max_len].rstrip("-") or "music"


def cmd_models(_: argparse.Namespace) -> int:
    for spec in MODELS.values():
        mark = "★" if spec.key == DEFAULT_MODEL else " "
        print(f"{mark} {spec.key:<7} {spec.repo_id:<26} {spec.params:>5}  ~{spec.approx_ram_gb:.0f}GB RAM  {spec.note}")
    return 0


def cmd_generate(args: argparse.Namespace) -> int:
    from .generator import MusicGenerator

    prompts = list(args.prompt)
    if args.prompt_file:
        lines = Path(args.prompt_file).read_text(encoding="utf-8").splitlines()
        prompts += [l.strip() for l in lines if l.strip() and not l.startswith("#")]
    if not prompts:
        print("プロンプトを指定してください", file=sys.stderr)
        return 2

    config = GenerationConfig(
        duration=args.duration,
        guidance_scale=args.guidance,
        temperature=args.temperature,
        top_k=args.top_k,
        top_p=args.top_p,
        seed=args.seed,
    )
    generator = MusicGenerator(model=args.model, threads=args.threads)
    out_dir = Path(args.out_dir)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # バッチが大きいとメモリを食うので batch_size ごとに区切る
    for i in range(0, len(prompts), args.batch_size):
        for j, result in enumerate(generator.generate(prompts[i : i + args.batch_size], config)):
            name = f"{stamp}_{i + j:02d}_{slugify(result.prompt)}.wav"
            path = save_wav(out_dir / name, result.audio, result.sample_rate)
            print(f"{path}  ({result.duration_sec:.1f}s audio, {result.elapsed_sec:.1f}s compute)  {result.prompt}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="musicgen-cpu", description="CPU で MusicGen を動かす")
    parser.add_argument("-v", "--verbose", action="store_true")
    sub = parser.add_subparsers(dest="command", required=True)

    p_models = sub.add_parser("models", help="利用可能なモデル一覧")
    p_models.set_defaults(func=cmd_models)

    p_gen = sub.add_parser("generate", help="テキストから音楽を生成")
    p_gen.add_argument("prompt", nargs="*", help="英語のテキストプロンプト (複数可)")
    p_gen.add_argument("-f", "--prompt-file", help="1 行 1 プロンプトのファイル")
    p_gen.add_argument("-m", "--model", default=DEFAULT_MODEL, help=f"small/medium/large または HF リポジトリ ID (既定: {DEFAULT_MODEL})")
    p_gen.add_argument("-d", "--duration", type=float, default=8.0, help=f"秒数 (最大 {MAX_DURATION_SEC:.0f})")
    p_gen.add_argument("-o", "--out-dir", default="outputs")
    p_gen.add_argument("--seed", type=int)
    p_gen.add_argument("--guidance", type=float, default=3.0, help="classifier-free guidance の強さ")
    p_gen.add_argument("--temperature", type=float, default=1.0)
    p_gen.add_argument("--top-k", type=int, default=250)
    p_gen.add_argument("--top-p", type=float, default=0.0)
    p_gen.add_argument("--batch-size", type=int, default=1)
    p_gen.add_argument("--threads", type=int, help="torch のスレッド数 (既定: CPU コア数)")
    p_gen.set_defaults(func=cmd_generate)

    p_batch = sub.add_parser("batch", help="要件テキストファイルの全曲を連続生成")
    p_batch.add_argument("requirements", nargs="?", default="music_requirements.txt")
    p_batch.add_argument("--only", nargs="+", metavar="NAME", help="指定した상자だけ生成")
    p_batch.add_argument("--priority", type=int, choices=[1, 2, 3], help="この優先度以下だけ生成 (1 = 必須のみ)")
    p_batch.add_argument("--overwrite", action="store_true", help="既存ファイルも作り直す")
    p_batch.add_argument("--dry-run", action="store_true", help="生成せず対象一覧だけ表示")
    p_batch.add_argument("-o", "--out-dir", help="要件ファイルの output_dir を上書き")
    p_batch.add_argument("-m", "--model", help="要件ファイルの model を上書き")
    p_batch.add_argument("--threads", type=int)
    p_batch.set_defaults(func=cmd_batch)
    return parser


def cmd_batch(args: argparse.Namespace) -> int:
    from .batch import run_batch

    return run_batch(
        args.requirements,
        only=args.only,
        max_priority=args.priority,
        overwrite=args.overwrite,
        dry_run=args.dry_run,
        output_dir=args.out_dir,
        model=args.model,
        threads=args.threads,
    )


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        return args.func(args)
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
