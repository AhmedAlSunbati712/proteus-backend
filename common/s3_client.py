from __future__ import annotations

from io import BytesIO

import boto3
from PIL import Image
from botocore.config import Config

from .config import Settings


def _use_minio(settings: Settings) -> bool:
    """Use MinIO only when ENV is development and we have a non-localhost endpoint or are in dev."""
    if settings.ENV != "development":
        return False
    # In K8s, localhost is the pod; MinIO is a separate service. Prefer AWS if we have creds.
    ep = (settings.minio_endpoint or "").strip().lower()
    if "localhost" in ep or "127.0.0.1" in ep:
        if settings.s3_access_key_id and settings.s3_secret_access_key:
            return False  # Use real S3 when MinIO endpoint is localhost but AWS creds exist
    return True


class S3ImageStore:
    def __init__(self, settings: Settings) -> None:
        session = boto3.session.Session()
        use_minio = _use_minio(settings)
        config = {}
        client_kwargs: dict[str, object] = {
            "region_name": settings.aws_region,
        }
        if use_minio:
            client_kwargs["endpoint_url"] = settings.minio_endpoint
            client_kwargs["aws_access_key_id"] = settings.minio_root_user
            client_kwargs["aws_secret_access_key"] = settings.minio_root_password

            config = {"addressing_style": "path"}
        else:
            client_kwargs["aws_access_key_id"] = settings.s3_access_key_id
            client_kwargs["aws_secret_access_key"] = settings.s3_secret_access_key

        s3_config = Config(s3={**config})
        self._bucket = settings.s3_bucket
        self._client = session.client("s3", config=s3_config, **client_kwargs)

    def download_image(self, key: str) -> Image.Image:
        obj = self._client.get_object(Bucket=self._bucket, Key=key)
        data = obj["Body"].read()
        image = Image.open(BytesIO(data))
        return image.convert("RGBA")

    def upload_png(self, key: str, image: Image.Image) -> str:
        buffer = BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)

        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=buffer.getvalue(),
            ContentType="image/png",
        )
        return key
