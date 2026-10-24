"""音声書き出し。依存を増やさないよう標準ライブラリの wave を使う。"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np


def to_int16(audio: np.ndarray) -> np.ndarray:
    """float 波形 (-1〜1) を 16bit PCM に変換する。(channels, samples) も (samples,) も受け付ける。"""
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim == 2:
        audio = audio.T  # wave はインターリーブ (samples, channels) を期待する
    elif audio.ndim != 1:
        raise ValueError(f"想定外の波形 shape: {audio.shape}")
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak > 1.0:
        audio = audio / peak
    return (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2")


def save_wav(path: str | Path, audio: np.ndarray, sample_rate: int) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pcm = to_int16(audio)
    channels = 1 if pcm.ndim == 1 else pcm.shape[1]
    with wave.open(str(path), "wb") as f:
        f.setnchannels(channels)
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(pcm.tobytes())
    return path
