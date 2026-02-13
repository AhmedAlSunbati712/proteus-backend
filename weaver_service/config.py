from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    redis_url: str
    redis_queue: str
    redis_events_channel: str

    aws_region: str
    s3_bucket: str
    s3_result_prefix: str
    s3_endpoint_url: str | None
    s3_access_key_id: str | None
    s3_secret_access_key: str | None

    inference_backend: str
    catvton_model_id: str
    device: str

    log_level: str


def _env(name: str, default: str | None = None) -> str:
    value = os.getenv(name, default)
    if value is None:
        raise ValueError(f"Missing required env var: {name}")
    return value


def load_settings() -> Settings:
    return Settings(
        redis_url=_env("REDIS_URL", "redis://localhost:6379/0"),
        redis_queue=_env("REDIS_WEAVER_QUEUE", "queue:weaver_jobs"),
        redis_events_channel=_env("REDIS_EVENTS_CHANNEL", "events:job_done"),
        aws_region=_env("AWS_REGION", "us-east-1"),
        s3_bucket=_env("S3_BUCKET", "proteus-bucket"),
        s3_result_prefix=_env("S3_RESULT_PREFIX", "outputs/weaver"),
        s3_endpoint_url=os.getenv("S3_ENDPOINT_URL") or os.getenv("MINIO_ENDPOINT"),
        s3_access_key_id=os.getenv("AWS_ACCESS_KEY_ID") or os.getenv("MINIO_ROOT_USER"),
        s3_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY") or os.getenv("MINIO_ROOT_PASSWORD"),
        inference_backend=_env("INFERENCE_BACKEND", "stub").lower(),
        catvton_model_id=_env("CATVTON_MODEL_ID", "zhengchong/CatVTON"),
        device=_env("DEVICE", "cuda"),
        log_level=_env("LOG_LEVEL", "INFO"),
    )
