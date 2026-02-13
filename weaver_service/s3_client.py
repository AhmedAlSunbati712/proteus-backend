from __future__ import annotations

from io import BytesIO

import boto3
from PIL import Image

from .config import Settings


class S3ImageStore:
    def __init__(self, settings: Settings) -> None:
        session = boto3.session.Session()
        client_kwargs: dict[str, object] = {
            "region_name": settings.aws_region,
        }
        if settings.s3_endpoint_url:
            client_kwargs["endpoint_url"] = settings.s3_endpoint_url
        if settings.s3_access_key_id and settings.s3_secret_access_key:
            client_kwargs["aws_access_key_id"] = settings.s3_access_key_id
            client_kwargs["aws_secret_access_key"] = settings.s3_secret_access_key

        self._bucket = settings.s3_bucket
        self._client = session.client("s3", **client_kwargs)

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
