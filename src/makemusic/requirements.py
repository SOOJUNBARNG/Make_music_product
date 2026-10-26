"""要件テキストファイル (INI 形式) の読み込み。"""

from __future__ import annotations

import configparser
from dataclasses import dataclass
from pathlib import Path

SETTINGS_SECTION = "settings"

# ACE-Step 1.5 が受け付ける範囲
MIN_DURATION_SEC = 10.0
MAX_DURATION_SEC = 600.0
MAX_CAPTION_CHARS = 512


@dataclass
class Settings:
    output_dir: str = "music-source"
    seed: int | None = None
    default_duration: float = 60.0
    loop_crossfade: float = 2.0
    style: str = ""
    # ACE-Step のモデル構成 (L4 24GB 向けの既定値)
    dit_model: str = "acestep-v15-xl-turbo"
    lm_model: str = "acestep-5Hz-lm-1.7B"
    lm_backend: str = "vllm"
    inference_steps: int = 8
    shift: float = 3.0
    thinking: bool = True


@dataclass
class Track:
    name: str
    prompt: str = ""
    duration: float = 60.0
    priority: int = 1
    gain_db: float = 0.0
    seed: int | None = None
    copy_of: str | None = None
    bpm: int | None = None
    keyscale: str = ""
    timesignature: str = ""

    def caption(self, style: str) -> str:
        return f"{self.prompt}, {style}" if style else self.prompt


TRACK_KEYS = {
    "prompt", "duration", "priority", "gain_db", "seed", "copy_of", "bpm", "keyscale", "timesignature",
}


def _one_line(text: str) -> str:
    return " ".join(text.split())


def load_requirements(path: str | Path) -> tuple[Settings, list[Track]]:
    parser = configparser.ConfigParser(interpolation=None)
    parser.optionxform = str  # キーの大文字小文字を保つ
    with open(path, encoding="utf-8") as f:
        parser.read_file(f)

    d = Settings()
    settings = d
    if parser.has_section(SETTINGS_SECTION):
        s = parser[SETTINGS_SECTION]
        settings = Settings(
            output_dir=s.get("output_dir", d.output_dir),
            seed=s.getint("seed", fallback=None),
            default_duration=s.getfloat("default_duration", d.default_duration),
            loop_crossfade=s.getfloat("loop_crossfade", d.loop_crossfade),
            style=_one_line(s.get("style", "")),
            dit_model=s.get("dit_model", d.dit_model),
            lm_model=s.get("lm_model", d.lm_model),
            lm_backend=s.get("lm_backend", d.lm_backend),
            inference_steps=s.getint("inference_steps", d.inference_steps),
            shift=s.getfloat("shift", d.shift),
            thinking=s.getboolean("thinking", d.thinking),
        )

    names = [n for n in parser.sections() if n != SETTINGS_SECTION]
    tracks: list[Track] = []
    for name in names:
        sec = parser[name]
        unknown = set(sec.keys()) - TRACK_KEYS
        if unknown:
            raise ValueError(f"[{name}] 未知のキーがあります: {', '.join(sorted(unknown))}")
        track = Track(
            name=name,
            prompt=_one_line(sec.get("prompt", "")),
            duration=sec.getfloat("duration", settings.default_duration),
            priority=sec.getint("priority", 1),
            gain_db=sec.getfloat("gain_db", 0.0),
            seed=sec.getint("seed", fallback=None),
            copy_of=sec.get("copy_of") or None,
            bpm=sec.getint("bpm", fallback=None),
            keyscale=sec.get("keyscale", ""),
            timesignature=sec.get("timesignature", ""),
        )
        _validate(track, settings, names)
        tracks.append(track)
    return settings, tracks


def _validate(track: Track, settings: Settings, names: list[str]) -> None:
    if track.copy_of:
        if track.copy_of not in names:
            raise ValueError(f"[{track.name}] copy_of の参照先 [{track.copy_of}] がありません")
        return
    if not track.prompt:
        raise ValueError(f"[{track.name}] に prompt がありません")
    total = track.duration + settings.loop_crossfade
    if not MIN_DURATION_SEC <= total <= MAX_DURATION_SEC:
        raise ValueError(
            f"[{track.name}] duration + loop_crossfade ({total:.0f} 秒) は "
            f"{MIN_DURATION_SEC:.0f}〜{MAX_DURATION_SEC:.0f} 秒にしてください"
        )
    caption = track.caption(settings.style)
    if len(caption) > MAX_CAPTION_CHARS:
        raise ValueError(
            f"[{track.name}] prompt + style が {len(caption)} 文字です。{MAX_CAPTION_CHARS} 文字以内にしてください"
        )


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
