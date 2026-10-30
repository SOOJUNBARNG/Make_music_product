"""GPU も ACE-Step も無しで確認できる部分のテスト。"""

import sys
import types
import wave
from pathlib import Path

import numpy as np
import pytest

from makemusic.audio import make_loopable, normalize, save_wav
from makemusic.requirements import load_requirements, select_tracks
from makemusic.runner import run

ROOT = Path(__file__).resolve().parent.parent

SAMPLE = """
[settings]
output_dir = out
seed = 100
default_duration = 20
loop_crossfade = 1.0
style = instrumental
style_battle = playful battle

[title]
priority = 1
duration = 30
bpm = 90
keyscale = D major
prompt = warm theme,
    gayageum and koto

[scene]
priority = 2
gain_db = -6
prompt = calm background

[scene.openingJp]
priority = 2
copy_of = title

[goal]
priority = 3
duration = 12
loop = false
prompt = jingle

[battle]
priority = 3
duration = 12
style = battle
prompt = pounce
"""


@pytest.fixture
def req(tmp_path):
    path = tmp_path / "req.txt"
    path.write_text(SAMPLE, encoding="utf-8")
    return path


def test_load_requirements(req):
    settings, tracks = load_requirements(req)
    assert settings.dit_model == "acestep-v15-xl-turbo"  # 既定値
    title, scene, copy, goal, battle = tracks
    assert title.caption(settings) == "warm theme, gayageum and koto, instrumental"
    assert battle.caption(settings) == "pounce, playful battle"  # 名前付きスタイル
    assert (goal.loop, goal.crossfade(settings), title.crossfade(settings)) == (False, 0.0, 1.0)
    assert (title.bpm, title.keyscale) == (90, "D major")
    assert scene.duration == 20 and scene.gain_db == -6
    assert copy.copy_of == "title"


@pytest.mark.parametrize(
    "track, error",
    [
        ("[a]\nduration = 10\n", "prompt"),
        ("[a]\nprompt = x\nduration = 5\n", "10〜600"),
        ("[a]\nprompt = x\nduraton = 30\n", "未知のキー"),
        ("[a]\ncopy_of = nothing\n", "参照先"),
        (f"[a]\nprompt = {'x' * 600}\n", "512"),
        ("[a]\nprompt = x\nstyle = nope\n", "style_nope"),
    ],
)
def test_invalid_requirements(tmp_path, track, error):
    path = tmp_path / "bad.txt"
    path.write_text(track, encoding="utf-8")
    with pytest.raises(ValueError, match=error):
        load_requirements(path)


def test_bundled_requirements():
    settings, tracks = load_requirements(ROOT / "music_requirements.txt")
    # 음악 의뢰서 (2026-10-30): 66 상자、① 꼭 필요한 곡 16
    assert len(tracks) == 66
    assert sum(t.priority == 1 for t in tracks) == 16
    regions = {"title", "kr", "jp", "cn", "isle", "southsea", "indian", "eu", "naf", "atl", "nw", "waf"}
    by_name = {t.name: t for t in tracks}
    # 길이: 지역 곡 1분 30초~3분, 장면·시련 30초~1분, 목표 20~40초
    assert all(90 <= by_name[n].duration <= 180 for n in regions)
    events = [t for t in tracks if t.name not in regions and not t.copy_of]
    assert all(20 <= t.duration <= 60 for t in events)
    # 会話シーンの曲は台詞を邪魔しないよう全部小さめ
    assert all(t.gain_db < 0 for t in tracks if t.name.startswith("scene") and not t.copy_of)
    # 戦闘曲は「전투용 꼬리」、それ以外は「공통 꼬리」。goal はループしない短い曲
    assert {t.name for t in tracks if t.style == "battle"} == {"battle", "battle.boss"}
    assert "no real cat meow sounds" in by_name["kr"].caption(settings)
    assert "pouncing" in by_name["battle"].caption(settings)
    assert all(not t.loop for t in tracks if t.name.startswith("goal"))
    assert [t.name for t in select_tracks(tracks, max_priority=1)][:2] == ["title", "kr"]


class FakeBackend:
    def __init__(self):
        self.calls = []

    def generate(self, track, duration, seed):
        self.calls.append((track.name, duration, seed))
        sr = 1000
        t = np.arange(int(duration * sr)) / sr
        return np.stack([np.sin(2 * np.pi * 5 * t)] * 2).astype(np.float32), sr


def test_run_generates_loops_copies_and_resumes(req):
    backend = FakeBackend()
    loads = []

    def factory(settings):
        loads.append(settings)
        return backend

    assert run(req, factory) == 0
    out = req.parent / "out"
    # 生成はクロスフェード 1 秒ぶん長く頼み、仕上がりは指定どおりの長さ。loop = false は長く頼まない
    assert backend.calls == [("title", 31.0, 100), ("scene", 21.0, 101), ("goal", 12.0, 103), ("battle", 13.0, 104)]
    with wave.open(str(out / "title.wav")) as f:
        assert (f.getnchannels(), f.getnframes()) == (2, 30_000)
    assert (out / "scene.openingJp.wav").read_bytes() == (out / "title.wav").read_bytes()
    assert not list(out.glob("*.part"))

    with wave.open(str(out / "goal.wav")) as f:
        assert f.getnframes() == 12_000

    # 2 回目は全部スキップされ、モデルも読み込まない
    assert run(req, factory) == 0
    assert len(loads) == 1 and len(backend.calls) == 4

    # --only + --overwrite は同じシードで作り直す
    assert run(req, factory, only=["scene"], overwrite=True) == 0
    assert backend.calls[-1] == ("scene", 21.0, 101)


def test_run_regenerates_when_requirements_change(req):
    backend = FakeBackend()
    assert run(req, lambda s: backend) == 0
    out = req.parent / "out"
    # 要件の記録が無い古いファイル (例: 以前のプロンプトで作った曲) も作り直す対象
    (out / "scene.wav.json").unlink()
    req.write_text(req.read_text(encoding="utf-8").replace("warm theme", "bright theme"), encoding="utf-8")
    backend.calls.clear()
    assert run(req, lambda s: backend) == 0
    # プロンプトを変えた title と記録の無い scene だけ作り直し、title のコピーもやり直す
    assert [c[0] for c in backend.calls] == ["title", "scene"]
    assert (out / "scene.openingJp.wav").read_bytes() == (out / "title.wav").read_bytes()


def test_run_continues_after_failure(req):
    class Flaky(FakeBackend):
        def generate(self, track, duration, seed):
            if track.name == "title":
                raise RuntimeError("boom")
            return super().generate(track, duration, seed)

    assert run(req, lambda s: Flaky()) == 1
    out = req.parent / "out"
    assert (out / "scene.wav").exists()
    assert not (out / "title.wav").exists()
    assert not (out / "scene.openingJp.wav").exists()  # コピー元が無いので失敗扱い


def test_dry_run_loads_nothing(req, capsys):
    assert run(req, lambda s: pytest.fail("ロードされてはいけない"), dry_run=True) == 0
    assert "copy of title" in capsys.readouterr().out


def test_acestep_backend_follows_documented_api(monkeypatch, req):
    """ACE-Step 1.5 の docs/en/INFERENCE.md にある API の形どおりに呼んでいるか。"""
    calls = {}

    class Handler:
        def initialize_service(self, **kw):
            calls["dit"] = kw
            return "ok"

    class LLM:
        def initialize(self, **kw):
            calls["llm"] = kw
            return "ok"

    class Params:
        def __init__(self, **kw):
            calls["params"] = kw

    class Config:
        def __init__(self, **kw):
            calls["config"] = kw

    def generate_music(dit, llm, params, config, save_dir):
        calls["save_dir"] = save_dir
        audio = {"tensor": np.zeros((2, 480), dtype=np.float32), "sample_rate": 48000}
        return types.SimpleNamespace(success=True, error=None, audios=[audio])

    fake = {
        "acestep": types.ModuleType("acestep"),
        "acestep.handler": types.SimpleNamespace(AceStepHandler=Handler),
        "acestep.llm_inference": types.SimpleNamespace(LLMHandler=LLM),
        "acestep.inference": types.SimpleNamespace(
            GenerationParams=Params, GenerationConfig=Config, generate_music=generate_music
        ),
    }
    for name, mod in fake.items():
        monkeypatch.setitem(sys.modules, name, mod)

    from makemusic.acestep_backend import AceStepBackend

    settings, tracks = load_requirements(req)
    backend = AceStepBackend(settings, "/opt/ace", device="cuda")
    audio, sr = backend.generate(tracks[0], 31.0, 100)

    assert calls["dit"] == {"project_root": "/opt/ace", "config_path": "acestep-v15-xl-turbo", "device": "cuda"}
    assert calls["llm"]["checkpoint_dir"] == "/opt/ace/checkpoints"
    assert calls["llm"]["lm_model_path"] == "acestep-5Hz-lm-1.7B"
    p = calls["params"]
    assert p["instrumental"] is True and p["lyrics"] == "[Instrumental]"
    assert (p["duration"], p["seed"], p["bpm"], p["keyscale"]) == (31.0, 100, 90, "D major")
    assert calls["config"]["seeds"] == [100] and calls["config"]["use_random_seed"] is False
    assert audio.shape == (2, 480) and sr == 48000


def test_make_loopable_seam_is_continuous():
    sr = 1000
    audio = np.sin(np.linspace(0, 40 * np.pi, 5 * sr, dtype=np.float32))[None, :]
    out = make_loopable(audio, sr, 0.5)
    assert out.shape[-1] == 4500
    np.testing.assert_allclose(out[0, -1], audio[0, 4499])
    np.testing.assert_allclose(out[0, 0], audio[0, 4500], atol=1e-6)


def test_normalize_and_save_stereo(tmp_path):
    audio = np.array([[0.1, -0.5], [0.2, 0.0]], dtype=np.float32)
    out = normalize(audio, peak_db=0.0, gain_db=-6.0)
    assert np.isclose(np.max(np.abs(out)), 10 ** (-6 / 20), atol=1e-6)
    with wave.open(str(save_wav(tmp_path / "a.wav", out, 48000))) as f:
        assert (f.getnchannels(), f.getframerate(), f.getnframes()) == (2, 48000, 2)
