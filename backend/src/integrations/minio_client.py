import asyncio
import json
import logging
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class ObjectStoreClient:
    BUCKETS = ["models", "holdout", "evidence", "reports"]

    def __init__(self, endpoint_url: str, access_key: str, secret_key: str):
        self.endpoint_url = endpoint_url
        # Use boto3 in a threadpool since it's synchronous
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=Config(signature_version="s3v4"),
        )

    async def ensure_buckets(self):
        """Create all required buckets if they don't exist."""

        def _create_buckets():
            existing = [b["Name"] for b in self.client.list_buckets().get("Buckets", [])]
            for bucket in self.BUCKETS:
                if bucket not in existing:
                    try:
                        self.client.create_bucket(Bucket=bucket)
                        logger.info(f"Created bucket: {bucket}")
                    except ClientError as e:
                        logger.error(f"Failed to create bucket {bucket}: {e}")
                        raise

        await asyncio.to_thread(_create_buckets)

    async def upload_file(
        self, bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream"
    ) -> str:
        def _upload():
            self.client.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)
            return f"{self.endpoint_url}/{bucket}/{key}"

        return await asyncio.to_thread(_upload)

    async def download_file(self, bucket: str, key: str) -> bytes:
        def _download():
            response = self.client.get_object(Bucket=bucket, Key=key)
            return response["Body"].read()

        return await asyncio.to_thread(_download)

    async def list_objects(self, bucket: str, prefix: str = "") -> list[dict]:
        def _list():
            try:
                response = self.client.list_objects_v2(Bucket=bucket, Prefix=prefix)
                return response.get("Contents", [])
            except ClientError as e:
                logger.error(f"Failed to list objects in {bucket}/{prefix}: {e}")
                return []

        return await asyncio.to_thread(_list)

    async def upload_model_artifact(
        self, model_name: str, version: str, model_bytes: bytes, metadata: dict[str, Any]
    ) -> str:
        model_key = f"{model_name}/{version}/model.onnx"
        meta_key = f"{model_name}/{version}/metadata.json"

        url = await self.upload_file("models", model_key, model_bytes, "application/octet-stream")
        await self.upload_file(
            "models", meta_key, json.dumps(metadata).encode("utf-8"), "application/json"
        )

        return url

    async def download_holdout_set(self, version: str) -> bytes:
        key = f"{version}/data.parquet"
        return await self.download_file("holdout", key)

    async def health_check(self) -> bool:
        def _check():
            try:
                self.client.list_buckets()
                return True
            except Exception as e:
                logger.error(f"MinIO health check failed: {e}")
                return False

        return await asyncio.to_thread(_check)
