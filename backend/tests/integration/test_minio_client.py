import pytest
from src.integrations.minio_client import ObjectStoreClient
from src.config import settings

@pytest.mark.asyncio
async def test_minio_client():
    secret = settings.MINIO_SECRET_KEY.get_secret_value() if settings.MINIO_SECRET_KEY else "minioadmin"
    client = ObjectStoreClient(f"http://{settings.MINIO_ENDPOINT}", settings.MINIO_ACCESS_KEY, secret)
    
    is_healthy = await client.health_check()
    assert is_healthy, "MinIO health check failed"
    
    await client.ensure_buckets()
    
    # Test upload and download
    data = b"test data"
    url = await client.upload_file("evidence", "test.txt", data, "text/plain")
    assert url.endswith("evidence/test.txt")
    
    downloaded = await client.download_file("evidence", "test.txt")
    assert downloaded == data
