"""モデルをダウンロードせずに確認できる部分のテスト。"""

import wave

import numpy as np
import pytest

from musicgen_cpu.audio import save_wav, to_int16
from musicgen_cpu.cli import build_parser, slugify
from musicgen_cpu.config import GenerationConfig, resolve_model


def test_max_new_tokens_is_50_per_second():
    assert GenerationConfig(duration=8).max_new_tokens == 400
    assert GenerationConfig(duration=0.5).max_new_tokens == 25


@pytest.mark.parametrize("duration", [0, -1, 31])
def test_duration_out_of_range(duration):
    with pytest.raises(ValueError):
        GenerationConfig(duration=duration)


def test_resolve_model():
    assert resolve_model("small").repo_id == "facebook/musicgen-small"
    assert resolve_model("facebook/musicgen-medium").key == "medium"
    assert resolve_model("someone/custom-musicgen").repo_id == "someone/custom-musicgen"


def test_to_int16_normalizes_and_interleaves():
    stereo = np.array([[0.0, 2.0], [-1.0, 0.5]], dtype=np.float32)  # (channels, samples)
    pcm = to_int16(stereo)
    assert pcm.shape == (2, 2)  # (samples, channels)
    assert pcm.max() == 32767  # 2.0 がピーク正規化される


def test_save_wav_roundtrip(tmp_path):
    sr = 32000
    audio = np.sin(np.linspace(0, 2 * np.pi * 440, sr)).astype(np.float32)[None, :]
    path = save_wav(tmp_path / "sub" / "a.wav", audio, sr)
    with wave.open(str(path)) as f:
        assert f.getframerate() == sr
        assert f.getnchannels() == 1
        assert f.getnframes() == sr


def test_slugify():
    assert slugify("Lo-fi hip hop, chill beats!") == "lo-fi-hip-hop-chill-beats"
    assert slugify("日本語") == "music"


def test_parser_defaults():
    args = build_parser().parse_args(["generate", "lofi piano"])
    assert args.model == "small"
    assert args.duration == 8.0
