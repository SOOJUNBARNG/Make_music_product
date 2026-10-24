"""MusicGen を CPU で動かす生成器。"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from dataclasses import dataclass, replace

import numpy as np

from .config import (
    DEFAULT_MODEL,
    MAX_DURATION_SEC,
    TOKENS_PER_SECOND,
    GenerationConfig,
    ModelSpec,
    resolve_model,
)

logger = logging.getLogger(__name__)


def default_threads() -> int:
    """Apple Silicon では高性能コア数を使う。効率コアまで使うと逆に遅くなる。"""
    if sys.platform == "darwin":
        try:
            out = subprocess.run(
                ["sysctl", "-n", "hw.perflevel0.physicalcpu"], capture_output=True, text=True, check=True
            )
            return max(1, int(out.stdout.strip()))
        except (OSError, ValueError, subprocess.CalledProcessError):
            pass
    return os.cpu_count() or 1


@dataclass
class GenerationResult:
    prompt: str
    audio: np.ndarray  # (channels, samples), float32
    sample_rate: int
    elapsed_sec: float

    @property
    def duration_sec(self) -> float:
        return self.audio.shape[-1] / self.sample_rate


class MusicGenerator:
    """テキストから音楽を生成する。モデルは初回の generate 時に遅延ロードする。"""

    def __init__(self, model: str = DEFAULT_MODEL, threads: int | None = None) -> None:
        self.spec: ModelSpec = resolve_model(model)
        self.threads = threads or default_threads()
        self._model = None
        self._processor = None

    @property
    def sample_rate(self) -> int:
        self._load()
        return self._model.config.audio_encoder.sampling_rate

    def _load(self) -> None:
        if self._model is not None:
            return
        import torch
        from transformers import AutoProcessor, MusicgenForConditionalGeneration

        torch.set_num_threads(self.threads)
        logger.info("モデルをロード中: %s (threads=%d)", self.spec.repo_id, self.threads)
        start = time.perf_counter()
        self._processor = AutoProcessor.from_pretrained(self.spec.repo_id)
        self._model = MusicgenForConditionalGeneration.from_pretrained(self.spec.repo_id)
        # CPU では半精度が遅い/未対応の演算があるため fp32 に揃える
        self._model.to("cpu", dtype=torch.float32).eval()
        logger.info("ロード完了 (%.1fs)", time.perf_counter() - start)

    def generate(
        self, prompts: str | list[str], config: GenerationConfig | None = None
    ) -> list[GenerationResult]:
        """プロンプトごとに 1 曲生成する。複数プロンプトはバッチでまとめて推論する。"""
        import torch

        config = config or GenerationConfig()
        if isinstance(prompts, str):
            prompts = [prompts]
        if not prompts:
            raise ValueError("プロンプトが空です")

        self._load()
        if config.seed is not None:
            torch.manual_seed(config.seed)

        inputs = self._processor(text=prompts, padding=True, return_tensors="pt")
        start = time.perf_counter()
        waves = self._run(inputs, config)
        elapsed = time.perf_counter() - start
        sr = self.sample_rate
        return [
            GenerationResult(prompt=p, audio=w, sample_rate=sr, elapsed_sec=elapsed)
            for p, w in zip(prompts, waves)
        ]

    def generate_long(
        self,
        prompt: str,
        duration: float,
        config: GenerationConfig | None = None,
        chunk_seconds: float = MAX_DURATION_SEC,
        overlap_seconds: float = 10.0,
    ) -> GenerationResult:
        """30 秒を超える曲を作る。直前 overlap_seconds 秒を音声プロンプトにして続きを生成し、つなげていく。"""
        import torch

        config = config or GenerationConfig()
        if not 0 <= overlap_seconds < chunk_seconds <= MAX_DURATION_SEC:
            raise ValueError("0 <= overlap_seconds < chunk_seconds <= 30 にしてください")
        if duration <= 0:
            raise ValueError(f"duration は正の値で指定してください: {duration}")

        self._load()
        sr = self.sample_rate
        if config.seed is not None:
            torch.manual_seed(config.seed)
        start = time.perf_counter()

        first = replace(config, duration=min(duration, chunk_seconds), seed=None)
        inputs = self._processor(text=[prompt], padding=True, return_tensors="pt")
        audio = self._run(inputs, first)[0]
        target = int(round(duration * sr))
        overlap = int(round(overlap_seconds * sr))

        while audio.shape[-1] < target:
            new_sec = min(chunk_seconds - overlap_seconds, (target - audio.shape[-1]) / sr)
            new_sec = max(new_sec, 1.0 / TOKENS_PER_SECOND)
            context = audio[0, -overlap:] if overlap else audio[0, :0]
            inputs = self._processor(
                text=[prompt], audio=[context], sampling_rate=sr, padding=True, return_tensors="pt"
            )
            out = self._run(inputs, replace(config, duration=new_sec, seed=None))[0]
            # 出力には音声プロンプト部分も含まれるので、末尾の新規部分だけ取り出す
            new_samples = min(int(round(new_sec * sr)), out.shape[-1])
            audio = np.concatenate([audio, out[:, -new_samples:]], axis=-1)
            logger.info("継ぎ足し: %.1f / %.1f 秒", audio.shape[-1] / sr, duration)

        return GenerationResult(
            prompt=prompt, audio=audio[:, :target], sample_rate=sr, elapsed_sec=time.perf_counter() - start
        )

    def _run(self, inputs, config: GenerationConfig) -> np.ndarray:
        import torch

        gen_kwargs = dict(
            do_sample=True,
            guidance_scale=config.guidance_scale,
            temperature=config.temperature,
            top_k=config.top_k,
            max_new_tokens=config.max_new_tokens,
        )
        if config.top_p > 0:
            gen_kwargs["top_p"] = config.top_p

        logger.info("生成中: %.1f 秒分", config.duration)
        start = time.perf_counter()
        with torch.inference_mode():
            audio = self._model.generate(**inputs, **gen_kwargs)
        logger.info("生成完了 (%.1fs)", time.perf_counter() - start)
        return audio.cpu().numpy().astype(np.float32)  # (batch, channels, samples)
