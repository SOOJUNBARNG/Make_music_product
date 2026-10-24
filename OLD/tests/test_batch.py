"""要件ファイルの読み込みと後処理のテスト (モデル不要)。"""

from pathlib import Path

import numpy as np
import pytest

from musicgen_cpu.batch import load_requirements, needs_chaining, run_batch, select_tracks
from musicgen_cpu.postprocess import make_loopable, normalize

ROOT = Path(__file__).resolve().parent.parent

SAMPLE = """
[settings]
model = small
output_dir = out
default_duration = 40
style = instrumental, no vocals

[title]
priority = 1
duration = 90
prompt = warm theme,
    gayageum and koto

[scene]
priority = 1
gain_db = -6
prompt = calm background

[scene.openingJp]
priority = 2
copy_of = title

[goal.0]
priority = 3
prompt = jingle
"""


@pytest.fixture
def req(tmp_path):
    path = tmp_path / "req.txt"
    path.write_text(SAMPLE, encoding="utf-8")
    return path


def test_load_requirements(req):
    settings, tracks = load_requirements(req)
    assert settings.output_dir == "out"
    assert [t.name for t in tracks] == ["title", "scene", "scene.openingJp", "goal.0"]
    title = tracks[0]
    assert title.prompt == "warm theme, gayageum and koto"  # 複数行が 1 行に
    assert title.full_prompt(settings.style) == "warm theme, gayageum and koto, instrumental, no vocals"
    assert tracks[1].duration == 40  # default_duration
    assert tracks[1].gain_db == -6
    assert tracks[2].copy_of == "title"


def test_select_tracks_priority_and_copy_last(req):
    _, tracks = load_requirements(req)
    assert [t.name for t in select_tracks(tracks, max_priority=1)] == ["title", "scene"]
    assert [t.name for t in select_tracks(tracks, only=["scene.openingJp", "title"])] == ["title", "scene.openingJp"]
    with pytest.raises(ValueError):
        select_tracks(tracks, only=["nope"])


def test_missing_prompt_is_error(tmp_path):
    path = tmp_path / "bad.txt"
    path.write_text("[kr]\nduration = 10\n", encoding="utf-8")
    with pytest.raises(ValueError, match="prompt"):
        load_requirements(path)


def test_dry_run_creates_nothing(req, capsys):
    assert run_batch(req, dry_run=True) == 0
    assert "copy of title" in capsys.readouterr().out
    assert not (req.parent / "out").exists()


def test_bundled_requirements_cover_all_45_boxes():
    _, tracks = load_requirements(ROOT / "music_requirements.txt")
    assert len(tracks) == 45
    assert sum(t.priority == 1 for t in tracks) == 10


def test_bundled_requirements_fit_in_one_generation():
    settings, tracks = load_requirements(ROOT / "music_requirements.txt")
    too_long = [t.name for t in tracks if not t.copy_of and needs_chaining(t, settings)]
    assert too_long == []


def test_make_loopable_seam_is_continuous():
    sr = 1000
    audio = np.sin(np.linspace(0, 40 * np.pi, 5 * sr, dtype=np.float32))[None, :]
    out = make_loopable(audio, sr, 0.5)
    assert out.shape[-1] == 4500
    # ループの継ぎ目 (末尾→先頭) が元の曲の連続した区間と一致する
    np.testing.assert_allclose(out[0, -1], audio[0, 4499])
    np.testing.assert_allclose(out[0, 0], audio[0, 4500], atol=1e-6)


def test_normalize_gain():
    audio = np.array([[0.1, -0.5]], dtype=np.float32)
    out = normalize(audio, peak_db=0.0, gain_db=-6.0)
    assert np.isclose(np.max(np.abs(out)), 10 ** (-6 / 20), atol=1e-6)
