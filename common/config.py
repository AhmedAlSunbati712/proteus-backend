from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    redis_url: str
    redis_queue: str
    redis_events_channel: str

    ENV: str
    
    minio_endpoint: str
    minio_root_user: str
    minio_root_password: str
    
    aws_region: str
    s3_bucket: str
    s3_result_prefix: str
    s3_endpoint_url: str | None
    s3_access_key_id: str | None
    s3_secret_access_key: str | None

    inference_backend: str
    catvton_model_id: str
    catvton_model_dir: str
    catvton_model_variant: str
    catvton_base_model_path: str
    mixed_precision: str
    allow_tf32: bool
    num_inference_steps: int
    guidance_scale: float
    width: int
    height: int
    seed: int
    device: str

    log_level: str


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Missing required env var: {name}")
    return value


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_settings() -> Settings:
    isDev = _env("ENV", "development") == "development"
    return Settings(
        redis_url=_env("REDIS_URL", "redis://localhost:6379/0"),
        redis_queue=_env("REDIS_WEAVER_QUEUE", "queue:weaver_jobs"),
        redis_events_channel=_env("REDIS_EVENTS_CHANNEL", "events:job_done"),
        ENV=_env("ENV", "development"),
        minio_endpoint=_env("MINIO_ENDPOINT", "http://localhost:9000"),
        minio_root_user=_env("MINIO_ROOT_USER", "minioadmin"),
        minio_root_password=_env("MINIO_ROOT_PASSWORD", "minioadmin"),
        aws_region=_env("AWS_REGION", "us-east-1"),
        s3_bucket=_env("S3_BUCKET", "proteus-bucket"),
        s3_result_prefix=_env("S3_RESULT_PREFIX", "outputs/weaver"),
        s3_endpoint_url=os.getenv("S3_ENDPOINT_URL"),
        s3_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        s3_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        inference_backend=_env("INFERENCE_BACKEND", "stub").lower(),
        catvton_model_id=_env("CATVTON_MODEL_ID", "zhengchong/CatVTON-MaskFree"),
        catvton_model_dir=_env("CATVTON_MODEL_DIR", "weaver_service/models/CatVTON-MaskFree"),
        catvton_model_variant=_env("CATVTON_MODEL_VARIANT", "mix-48k-1024"),
        catvton_base_model_path=_env("CATVTON_BASE_MODEL_PATH", "timbrooks/instruct-pix2pix"),
        mixed_precision=_env("MIXED_PRECISION", "bf16"),
        allow_tf32=_env_bool("ALLOW_TF32", True),
        num_inference_steps=int(_env("NUM_INFERENCE_STEPS", "50")),
        guidance_scale=float(_env("GUIDANCE_SCALE", "2.5")),
        width=int(_env("WIDTH", "768")),
        height=int(_env("HEIGHT", "1024")),
        seed=int(_env("SEED", "-1")),
        device=_env("DEVICE", "cuda"),
        log_level=_env("LOG_LEVEL", "INFO"),
    )
