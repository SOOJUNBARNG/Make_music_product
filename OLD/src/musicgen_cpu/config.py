"""モデル定義と生成パラメータ。"""

from __future__ import annotations

from dataclasses import dataclass

# MusicGen の EnCodec は 32kHz 音声を 50 フレーム/秒でトークン化する
TOKENS_PER_SECOND = 50
# 学習時の最大長。これを超えると品質が崩れる
MAX_DURATION_SEC = 30.0


@dataclass(frozen=True)
class ModelSpec:
    key: str
    repo_id: str
    params: str
    # fp32 で推論したときのおおよその RAM 使用量 (GB)
    approx_ram_gb: float
    cpu_friendly: bool
    note: str


MODELS: dict[str, ModelSpec] = {
    spec.key: spec
    for spec in [
        ModelSpec(
            key="small",
            repo_id="facebook/musicgen-small",
            params="300M",
            approx_ram_gb=2.0,
            cpu_friendly=True,
            note="CPU 推奨。8GB RAM の Mac でも動作",
        ),
        ModelSpec(
            key="medium",
            repo_id="facebook/musicgen-medium",
            params="1.5B",
            approx_ram_gb=7.0,
            cpu_friendly=False,
            note="高品質だが CPU では遅い。16GB 以上の RAM 推奨",
        ),
        ModelSpec(
            key="large",
            repo_id="facebook/musicgen-large",
            params="3.3B",
            approx_ram_gb=14.0,
            cpu_friendly=False,
            note="GPU 前提",
        ),
    ]
}

DEFAULT_MODEL = "small"


def resolve_model(name: str) -> ModelSpec:
    """'small' のような短縮名、または HF リポジトリ ID からモデルを引く。"""
    if name in MODELS:
        return MODELS[name]
    for spec in MODELS.values():
        if spec.repo_id == name:
            return spec
    # 未登録のリポジトリ (fine-tune 版など) もそのまま使えるようにする
    return ModelSpec(
        key=name,
        repo_id=name,
        params="?",
        approx_ram_gb=0.0,
        cpu_friendly=False,
        note="未登録モデル",
    )


@dataclass
class GenerationConfig:
    duration: float = 8.0
    guidance_scale: float = 3.0
    temperature: float = 1.0
    top_k: int = 250
    top_p: float = 0.0
    seed: int | None = None

    def __post_init__(self) -> None:
        if not 0 < self.duration <= MAX_DURATION_SEC:
            raise ValueError(f"duration は 0〜{MAX_DURATION_SEC} 秒で指定してください: {self.duration}")
        if self.temperature <= 0:
            raise ValueError(f"temperature は正の値で指定してください: {self.temperature}")

    @property
    def max_new_tokens(self) -> int:
        return int(round(self.duration * TOKENS_PER_SECOND))
