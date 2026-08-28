import hashlib
import io
import json
from datetime import UTC, datetime

import pandas as pd

from src.integrations.minio_client import ObjectStoreClient


class HoldoutManager:
    def __init__(self, object_store: ObjectStoreClient):
        self.object_store = object_store

    async def create_holdout(self, data: pd.DataFrame, version: str, target_col: str = "is_abusive") -> str:
        """
        Creates a versioned holdout dataset, computes its hash, and uploads to MinIO along with a manifest.
        """
        # Convert to parquet bytes
        buffer = io.BytesIO()
        data.to_parquet(buffer, index=False)
        parquet_bytes = buffer.getvalue()

        # Compute SHA-256
        sha256_hash = hashlib.sha256(parquet_bytes).hexdigest()

        # Compute class distribution
        class_dist = {}
        if target_col in data.columns:
            class_dist = data[target_col].value_counts(normalize=True).to_dict()
            # convert keys to strings if needed
            class_dist = {str(k): float(v) for k, v in class_dist.items()}

        manifest = {
            "version": version,
            "hash": sha256_hash,
            "row_count": len(data),
            "class_distribution": class_dist,
            "created_at": datetime.now(UTC).isoformat()
        }

        # Upload
        data_key = f"{version}/data.parquet"
        manifest_key = f"{version}/manifest.json"

        url = await self.object_store.upload_file("holdout", data_key, parquet_bytes, "application/octet-stream")
        await self.object_store.upload_file("holdout", manifest_key, json.dumps(manifest).encode('utf-8'), "application/json")

        return url

    async def load_holdout(self, version: str) -> tuple[pd.DataFrame, dict]:
        """
        Downloads a holdout set, verifies its integrity, and returns the DataFrame and manifest.
        """
        data_key = f"{version}/data.parquet"
        manifest_key = f"{version}/manifest.json"

        parquet_bytes = await self.object_store.download_file("holdout", data_key)
        manifest_bytes = await self.object_store.download_file("holdout", manifest_key)

        manifest = json.loads(manifest_bytes.decode('utf-8'))

        # Verify hash
        actual_hash = hashlib.sha256(parquet_bytes).hexdigest()
        if actual_hash != manifest["hash"]:
            raise ValueError(f"Hash mismatch for holdout {version}. Expected {manifest['hash']}, got {actual_hash}")

        # Parse parquet
        data = pd.read_parquet(io.BytesIO(parquet_bytes))

        return data, manifest

    async def list_versions(self) -> list[dict]:
        """
        Lists all available holdout versions.
        """
        objects = await self.object_store.list_objects("holdout")
        versions = []
        for obj in objects:
            key = obj["Key"]
            if key.endswith("manifest.json"):
                manifest_bytes = await self.object_store.download_file("holdout", key)
                manifest = json.loads(manifest_bytes.decode('utf-8'))
                versions.append(manifest)

        return sorted(versions, key=lambda x: x.get("created_at", ""), reverse=True)

    def verify_no_overlap(self, train_data: pd.DataFrame, holdout: pd.DataFrame, key_col: str) -> bool:
        """
        Verifies that there is no data leakage (no overlapping keys) between train and holdout sets.
        """
        train_keys = set(train_data[key_col])
        holdout_keys = set(holdout[key_col])

        overlap = train_keys.intersection(holdout_keys)
        if len(overlap) > 0:
            return False

        return True
