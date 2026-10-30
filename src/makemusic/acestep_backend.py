"""ACE-Step 1.5 の呼び出し。GPU の VM 上で、ACE-Step-1.5 の環境 (uv) から動かす。"""

from __future__ import annotations

import logging
import tempfile
import time
from pathlib import Path

import numpy as np

from .requirements import Settings, Track

logger = logging.getLogger(__name__)


class AceStepBackend:
    """DiT と LM を 1 回だけ読み込み、曲ごとに generate_music を呼ぶ。"""

    def __init__(self, settings: Settings, acestep_root: str | Path, device: str = "cuda") -> None:
        from acestep.handler import AceStepHandler
        from acestep.llm_inference import LLMHandler

        root = Path(acestep_root).resolve()
        start = time.perf_counter()
        logger.info("DiT をロード中: %s", settings.dit_model)
        self.dit = AceStepHandler()
        status = self.dit.initialize_service(
            project_root=str(root), config_path=settings.dit_model, device=device
        )
        logger.info("DiT: %s", status)

        logger.info("LM をロード中: %s (%s)", settings.lm_model, settings.lm_backend)
        self.llm = LLMHandler()
        status = self.llm.initialize(
            checkpoint_dir=str(root / "checkpoints"),
            lm_model_path=settings.lm_model,
            backend=settings.lm_backend,
            device=device,
        )
        logger.info("LM: %s", status)
        logger.info("ロード完了 (%.0fs)", time.perf_counter() - start)
        self.settings = settings

    def generate(self, track: Track, duration: float, seed: int | None) -> tuple[np.ndarray, int]:
        """1 曲生成して (channels, samples) の float32 波形とサンプルレートを返す。"""
        from acestep.inference import GenerationConfig, GenerationParams, generate_music

        s = self.settings
        params = GenerationParams(
            caption=track.caption(s),
            lyrics="[Instrumental]",
            instrumental=True,
            duration=duration,
            bpm=track.bpm,
            keyscale=track.keyscale,
            timesignature=track.timesignature,
            inference_steps=s.inference_steps,
            shift=s.shift,
            thinking=s.thinking,
            seed=-1 if seed is None else seed,
        )
        config = GenerationConfig(
            batch_size=1,
            use_random_seed=seed is None,
            seeds=None if seed is None else [seed],
            audio_format="flac",
        )
        # ACE-Step 自身も保存するので、使い捨ての場所に書かせて波形だけ受け取る
        with tempfile.TemporaryDirectory() as tmp:
            result = generate_music(self.dit, self.llm, params, config, save_dir=tmp)
        if not result.success:
            raise RuntimeError(f"ACE-Step の生成に失敗: {result.error}")
        audio = result.audios[0]
        tensor = audio["tensor"]
        wave = tensor.detach().cpu().float().numpy() if hasattr(tensor, "detach") else np.asarray(tensor)
        return wave.astype(np.float32), int(audio["sample_rate"])
