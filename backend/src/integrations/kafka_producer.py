import json
import logging
from collections.abc import Callable

from aiokafka import AIOKafkaProducer
from pydantic import BaseModel

from src.core.events import TOPIC_MAP
from src.core.exceptions import SchemaValidationError

logger = logging.getLogger(__name__)


class TypedKafkaProducer:
    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer: AIOKafkaProducer | None = None

    async def start(self):
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            request_timeout_ms=5000,
            retry_backoff_ms=100,
            acks="all",
        )
        await self.producer.start()
        logger.info(f"Kafka producer connected to {self.bootstrap_servers}")

    async def stop(self):
        if self.producer:
            await self.producer.stop()

    def _validate_event(self, topic: str, event: BaseModel):
        expected_class = TOPIC_MAP.get(topic)
        if not expected_class:
            raise SchemaValidationError(f"Topic {topic} is not mapped in TOPIC_MAP.")
        if not isinstance(event, expected_class):
            raise SchemaValidationError(
                f"Event for topic {topic} must be of type {expected_class.__name__}"
            )

    async def send_event(self, topic: str, event: BaseModel, key: str | None = None):
        if not self.producer:
            raise RuntimeError("Kafka producer is not started")

        self._validate_event(topic, event)
        await self.producer.send_and_wait(topic, value=event.model_dump(mode="json"), key=key)

    async def send_batch(
        self, topic: str, events: list[BaseModel], key_fn: Callable[[BaseModel], str | None]
    ):
        if not self.producer:
            raise RuntimeError("Kafka producer is not started")

        if not events:
            return

        for event in events:
            self._validate_event(topic, event)

        batch = self.producer.create_batch()
        for event in events:
            key = key_fn(event)
            key_bytes = key.encode("utf-8") if key else None
            value_bytes = json.dumps(event.model_dump(mode="json"), default=str).encode("utf-8")
            batch.append(key=key_bytes, value=value_bytes, timestamp_ms=None)

        await self.producer.send_batch(batch, topic, partition=None)

    async def health_check(self) -> bool:
        if not self.producer:
            return False
        try:
            cluster = await self.producer.client.fetch_all_metadata()
            return len(cluster.brokers()) > 0
        except Exception as e:
            logger.error(f"Kafka health check failed: {e}")
            return False
