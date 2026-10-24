"""要件テキストファイル (INI 形式) を読んで全曲を順番に生成する。"""

from __future__ import annotations

import configparser
import logging
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path

from .audio import save_wav
from .config import DEFAULT_MODEL, GenerationConfig

logger = logging.getLogger(__name__)

SETTINGS_SECTION = "settings"


@dataclass
class Settings:
    model: str = DEFAULT_MODEL
    output_dir: str = "music-source"
    seed: int | None = None
    chunk_seconds: float = 30.0
    overlap_seconds: float = 10.0
    loop_crossfade: float = 2.0
    default_duration: float = 45.0
    guidance: float = 3.0
    style: str = ""


@dataclass
class Track:
    name: str
    prompt: str = ""
    duration: float = 45.0
    priority: int = 1
    gain_db: float = 0.0
    seed: int | None = None
    copy_of: str | None = None
    extra: dict[str, str] = field(default_factory=dict)

    def full_prompt(self, style: str) -> str:
        return f"{self.prompt}, {style}" if style else self.prompt


def _one_line(text: str) -> str:
    return " ".join(text.split())


def load_requirements(path: str | Path) -> tuple[Settings, list[Track]]:
    parser = configparser.ConfigParser(interpolation=None, inline_comment_prefixes=None)
    parser.optionxform = str  # キーの大文字小文字を保つ
    with open(path, encoding="utf-8") as f:
        parser.read_file(f)

    settings = Settings()
    if parser.has_section(SETTINGS_SECTION):
        s = parser[SETTINGS_SECTION]
        settings = Settings(
            model=s.get("model", settings.model),
            output_dir=s.get("output_dir", settings.output_dir),
            seed=s.getint("seed", fallback=None),
            chunk_seconds=s.getfloat("chunk_seconds", settings.chunk_seconds),
            overlap_seconds=s.getfloat("overlap_seconds", settings.overlap_seconds),
            loop_crossfade=s.getfloat("loop_crossfade", settings.loop_crossfade),
            default_duration=s.getfloat("default_duration", settings.default_duration),
            guidance=s.getfloat("guidance", settings.guidance),
            style=_one_line(s.get("style", "")),
        )

    known = {"prompt", "duration", "priority", "gain_db", "seed", "copy_of"}
    tracks: list[Track] = []
    names = [n for n in parser.sections() if n != SETTINGS_SECTION]
    for name in names:
        sec = parser[name]
        track = Track(
            name=name,
            prompt=_one_line(sec.get("prompt", "")),
            duration=sec.getfloat("duration", settings.default_duration),
            priority=sec.getint("priority", 1),
            gain_db=sec.getfloat("gain_db", 0.0),
            seed=sec.getint("seed", fallback=None),
            copy_of=sec.get("copy_of") or None,
            extra={k: v for k, v in sec.items() if k not in known},
        )
        if track.copy_of:
            if track.copy_of not in names:
                raise ValueError(f"[{name}] copy_of の参照先 [{track.copy_of}] がありません")
        elif not track.prompt:
            raise ValueError(f"[{name}] に prompt がありません")
        if track.extra:
            logger.warning("[%s] 未知のキーを無視します: %s", name, ", ".join(track.extra))
        tracks.append(track)
    return settings, tracks


def select_tracks(
    tracks: list[Track], only: list[str] | None = None, max_priority: int | None = None
) -> list[Track]:
    selected = tracks
    if only:
        unknown = set(only) - {t.name for t in tracks}
        if unknown:
            raise ValueError(f"要件ファイルに無い상자です: {', '.join(sorted(unknown))}")
        selected = [t for t in selected if t.name in only]
    if max_priority is not None:
        selected = [t for t in selected if t.priority <= max_priority]
    # copy_of は参照先の生成後に処理したいので最後に回す
    return [t for t in selected if not t.copy_of] + [t for t in selected if t.copy_of]


def run_batch(
    requirements: str | Path,
    *,
    only: list[str] | None = None,
    max_priority: int | None = None,
    overwrite: bool = False,
    dry_run: bool = False,
    output_dir: str | None = None,
    model: str | None = None,
    threads: int | None = None,
) -> int:
    """全曲を順に作る。生成済みファイルはスキップするので、中断しても再実行で再開できる。"""
    from .generator import MusicGenerator
    from .postprocess import make_loopable, normalize

    settings, tracks = load_requirements(requirements)
    # 相対パスの output_dir は要件ファイルの場所を基準にする
    out_dir = Path(output_dir or settings.output_dir)
    if not out_dir.is_absolute():
        out_dir = Path(requirements).resolve().parent / out_dir
    todo = select_tracks(tracks, only, max_priority)

    print(f"要件: {requirements}  モデル: {model or settings.model}  出力: {out_dir}")
    print(f"対象 {len(todo)} 曲 / 合計 {sum(t.duration for t in todo if not t.copy_of) / 60:.1f} 分")
    if dry_run:
        for t in todo:
            what = f"copy of {t.copy_of}" if t.copy_of else f"{t.duration:>5.0f}s  {t.full_prompt(settings.style)}"
            print(f"  [{t.priority}] {t.name:<20} {what}")
        return 0

    generator = MusicGenerator(model=model or settings.model, threads=threads)
    failures: list[str] = []
    batch_start = time.perf_counter()
    for i, track in enumerate(todo, 1):
        path = out_dir / f"{track.name}.wav"
        head = f"[{i}/{len(todo)}] {track.name}"
        if path.exists() and not overwrite:
            print(f"{head}: 既存のためスキップ ({path.name})")
            continue
        try:
            if track.copy_of:
                src = out_dir / f"{track.copy_of}.wav"
                if not src.exists():
                    raise FileNotFoundError(f"コピー元 {src.name} がまだありません")
                shutil.copyfile(src, path)
                print(f"{head}: {src.name} をコピー")
                continue

            print(f"{head}: {track.duration:.0f}s 生成中...", flush=True)
            # 要件ファイル内の位置からシードを決め、--only で絞っても同じ曲が出るようにする
            seed = track.seed if track.seed is not None else (
                None if settings.seed is None else settings.seed + tracks.index(track)
            )
            config = GenerationConfig(
                duration=min(track.duration, settings.chunk_seconds),
                guidance_scale=settings.guidance,
                seed=seed,
            )
            # ループ用に切り落とす分だけ長めに作る
            result = generator.generate_long(
                track.full_prompt(settings.style),
                track.duration + settings.loop_crossfade,
                config,
                chunk_seconds=settings.chunk_seconds,
                overlap_seconds=settings.overlap_seconds,
            )
            audio = make_loopable(result.audio, result.sample_rate, settings.loop_crossfade)
            audio = normalize(audio, gain_db=track.gain_db)
            # 書き込み途中で止まっても壊れたファイルがスキップされないよう、一時ファイル経由で置く
            tmp = path.with_suffix(".wav.part")
            save_wav(tmp, audio, result.sample_rate)
            tmp.replace(path)
            print(f"{head}: 完了 {path.name} ({result.elapsed_sec:.0f}s)", flush=True)
        except Exception as e:  # 1 曲の失敗で全体を止めない
            logger.exception("%s の生成に失敗", track.name)
            print(f"{head}: 失敗 {e}", flush=True)
            failures.append(track.name)

    print(f"終了: {(time.perf_counter() - batch_start) / 60:.1f} 分, 失敗 {len(failures)} 件")
    if failures:
        print("失敗した상자: " + ", ".join(failures))
        return 1
    return 0
