import logging
from typing import Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, PointStruct

logger = logging.getLogger(__name__)

class QdrantVectorStore:
    COLLECTION_NAME = "chargeback_cases"

    def __init__(self, qdrant_url: str):
        self.client = AsyncQdrantClient(url=qdrant_url, timeout=10.0)

    async def ensure_collection(self):
        try:
            collections = await self.client.get_collections()
            if not any(c.name == self.COLLECTION_NAME for c in collections.collections):
                await self.client.create_collection(
                    collection_name=self.COLLECTION_NAME,
                    vectors_config=VectorParams(size=1536, distance=Distance.COSINE)
                )
                
                # Create payload indexes
                for field in ["reason_code", "network", "amount_bucket", "outcome"]:
                    await self.client.create_payload_index(
                        collection_name=self.COLLECTION_NAME,
                        field_name=field,
                        field_schema="keyword"
                    )
                logger.info(f"Created Qdrant collection {self.COLLECTION_NAME}")
        except Exception as e:
            logger.error(f"Failed to ensure Qdrant collection: {e}")
            raise

    async def upsert_case(self, case_id: str, embedding: list[float], payload: dict[str, Any]):
        point = PointStruct(
            id=case_id, # Qdrant supports UUID strings directly
            vector=embedding,
            payload=payload
        )
        await self.client.upsert(
            collection_name=self.COLLECTION_NAME,
            points=[point]
        )

    async def search_similar(
        self, query_embedding: list[float], reason_code: str | None = None, network: str | None = None, limit: int = 5
    ) -> list[dict[str, Any]]:
        conditions = []
        if reason_code:
            conditions.append(FieldCondition(key="reason_code", match=MatchValue(value=reason_code)))
        if network:
            conditions.append(FieldCondition(key="network", match=MatchValue(value=network)))
        
        query_filter = Filter(must=conditions) if conditions else None

        results = await self.client.query_points(
            collection_name=self.COLLECTION_NAME,
            query=query_embedding,
            query_filter=query_filter,
            limit=limit,
            with_payload=True
        )

        return [
            {
                "case_id": str(r.id),
                "score": r.score,
                "outcome": r.payload.get("outcome") if r.payload else None,
                "narrative_summary": r.payload.get("narrative_summary") if r.payload else None
            }
            for r in results.points
        ]

    async def health_check(self) -> bool:
        try:
            await self.client.get_collections()
            return True
        except Exception as e:
            logger.error(f"Qdrant health check failed: {e}")
            return False

    async def close(self):
        await self.client.close()
