"""音声の加工と書き出し。依存は numpy と標準ライブラリだけ。"""

from __future__ import annotations

import wave
from pathlib import Path

import numpy as np


def make_loopable(audio: np.ndarray, sample_rate: int, crossfade_sec: float) -> np.ndarray:
    """末尾 crossfade_sec 秒を先頭に重ねて切り落とす。

    結果を繰り返し再生すると、曲の終わり→(重ねておいた末尾)→始まり と途切れずにつながる。
    """
    n = int(round(crossfade_sec * sample_rate))
    if n <= 0:
        return audio
    if audio.shape[-1] < 2 * n:
        raise ValueError("クロスフェードが曲の長さに対して長すぎます")
    # 等パワーカーブで重ねて、つなぎ目の音量の落ち込みを防ぐ
    t = np.linspace(0.0, np.pi / 2, n, dtype=np.float32)
    fade_in, fade_out = np.sin(t), np.cos(t)
    head, tail = audio[..., :n], audio[..., -n:]
    out = audio[..., :-n].copy()
    out[..., :n] = head * fade_in + tail * fade_out
    return out


def normalize(audio: np.ndarray, peak_db: float = -1.0, gain_db: float = 0.0) -> np.ndarray:
    """ピークを peak_db にそろえた上で gain_db だけ下げ (上げ) る。"""
    peak = float(np.max(np.abs(audio))) if audio.size else 0.0
    if peak == 0.0:
        return audio
    scale = 10 ** ((peak_db + gain_db) / 20) / peak
    return (audio * scale).astype(np.float32)


def save_wav(path: str | Path, audio: np.ndarray, sample_rate: int) -> Path:
    """(channels, samples) の float 波形を 16bit PCM の WAV で保存する。"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim == 1:
        audio = audio[None, :]
    if audio.ndim != 2:
        raise ValueError(f"想定外の波形 shape: {audio.shape}")
    pcm = (np.clip(audio, -1.0, 1.0) * 32767).astype("<i2").T  # (samples, channels) にインターリーブ
    with wave.open(str(path), "wb") as f:
        f.setnchannels(pcm.shape[1])
        f.setsampwidth(2)
        f.setframerate(sample_rate)
        f.writeframes(pcm.tobytes())
    return path
