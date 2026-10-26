"""要件ファイルの全曲を順番に生成する。"""

from __future__ import annotations

import argparse
import logging
import shutil
import sys
import time
from pathlib import Path
from typing import Protocol

import numpy as np

from .audio import make_loopable, normalize, save_wav
from .requirements import Settings, Track, load_requirements, select_tracks

logger = logging.getLogger(__name__)


class Backend(Protocol):
    def generate(self, track: Track, duration: float, seed: int | None) -> tuple[np.ndarray, int]: ...


def track_seed(track: Track, settings: Settings, tracks: list[Track]) -> int | None:
    """要件ファイル内の位置からシードを決め、--only で絞っても同じ曲が出るようにする。"""
    if track.seed is not None:
        return track.seed
    if settings.seed is None:
        return None
    return settings.seed + tracks.index(track)


def resolve_output_dir(requirements: str | Path, settings: Settings, override: str | None) -> Path:
    # 相対パスの output_dir は要件ファイルの場所を基準にする
    out_dir = Path(override or settings.output_dir)
    if not out_dir.is_absolute():
        out_dir = Path(requirements).resolve().parent / out_dir
    return out_dir


def run(
    requirements: str | Path,
    backend_factory,
    *,
    only: list[str] | None = None,
    max_priority: int | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    output_dir: str | None = None,
) -> int:
    """生成済みファイルはスキップするので、Spot VM が止められても再実行で続きから再開できる。"""
    settings, tracks = load_requirements(requirements)
    out_dir = resolve_output_dir(requirements, settings, output_dir)
    todo = select_tracks(tracks, only, max_priority)

    print(f"要件: {requirements}  モデル: {settings.dit_model} + {settings.lm_model}  出力: {out_dir}")
    print(f"対象 {len(todo)} 曲 / 合計 {sum(t.duration for t in todo if not t.copy_of) / 60:.1f} 分", flush=True)
    if dry_run:
        for t in todo:
            what = f"copy of {t.copy_of}" if t.copy_of else f"{t.duration:>5.0f}s  {t.caption(settings.style)}"
            print(f"  [{t.priority}] {t.name:<20} {what}")
        return 0

    pending = [t for t in todo if overwrite or not (out_dir / f"{t.name}.wav").exists()]
    if not pending:
        print("すべて生成済みです")
        return 0
    backend: Backend | None = None
    failures: list[str] = []
    batch_start = time.perf_counter()
    for i, track in enumerate(todo, 1):
        path = out_dir / f"{track.name}.wav"
        head = f"[{i}/{len(todo)}] {track.name}"
        if track not in pending:
            print(f"{head}: 既存のためスキップ", flush=True)
            continue
        try:
            if track.copy_of:
                src = out_dir / f"{track.copy_of}.wav"
                if not src.exists():
                    raise FileNotFoundError(f"コピー元 {src.name} がまだありません")
                shutil.copyfile(src, path)
                print(f"{head}: {src.name} をコピー", flush=True)
                continue

            if backend is None:
                # モデルのロードは重いので、実際に生成する曲があるときだけ行う
                backend = backend_factory(settings)
            print(f"{head}: {track.duration:.0f}s 生成中...", flush=True)
            start = time.perf_counter()
            # ループ用に切り落とす分だけ長めに作る
            audio, sr = backend.generate(
                track, track.duration + settings.loop_crossfade, track_seed(track, settings, tracks)
            )
            audio = make_loopable(audio, sr, settings.loop_crossfade)
            audio = normalize(audio, gain_db=track.gain_db)
            # 書き込み途中で止まっても壊れたファイルがスキップされないよう、一時ファイル経由で置く
            tmp = path.with_suffix(".wav.part")
            save_wav(tmp, audio, sr)
            tmp.replace(path)
            print(
                f"{head}: 完了 {path.name} ({audio.shape[-1] / sr:.0f}s audio, {time.perf_counter() - start:.0f}s)",
                flush=True,
            )
        except Exception as e:  # 1 曲の失敗で全体を止めない
            logger.exception("%s の生成に失敗", track.name)
            print(f"{head}: 失敗 {e}", flush=True)
            failures.append(track.name)

    print(f"終了: {(time.perf_counter() - batch_start) / 60:.1f} 分, 失敗 {len(failures)} 件", flush=True)
    if failures:
        print("失敗した상자: " + ", ".join(failures))
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="要件ファイルの全曲を ACE-Step 1.5 で生成する")
    p.add_argument("requirements", nargs="?", default="music_requirements.txt")
    p.add_argument("--only", nargs="+", metavar="NAME", help="指定した상자だけ生成")
    p.add_argument("--priority", type=int, choices=[1, 2, 3], help="この優先度以下だけ生成 (1 = 必須のみ)")
    p.add_argument("--overwrite", action="store_true", help="既存ファイルも作り直す")
    p.add_argument("--dry-run", action="store_true", help="生成せず対象一覧だけ表示")
    p.add_argument("-o", "--out-dir", help="要件ファイルの output_dir を上書き")
    p.add_argument("--acestep-root", default="~/ACE-Step-1.5", help="ACE-Step-1.5 を clone した場所")
    p.add_argument("--device", default="cuda")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.INFO if args.verbose else logging.WARNING,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    def factory(settings: Settings):
        from .acestep_backend import AceStepBackend

        return AceStepBackend(settings, Path(args.acestep_root).expanduser(), device=args.device)

    try:
        return run(
            args.requirements,
            factory,
            only=args.only,
            max_priority=args.priority,
            overwrite=args.overwrite,
            dry_run=args.dry_run,
            output_dir=args.out_dir,
        )
    except ValueError as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 2
