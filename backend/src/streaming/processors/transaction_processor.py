import logging
from uuid import UUID

import faust

from src.config import settings
from src.integrations.redis_client import RedisClient
from src.streaming.app import app
from src.streaming.tables.amount_windows import get_amount_stats, update_amount_window
from src.streaming.tables.velocity_counters import (
    get_velocity,
    velocity_table_1h,
    velocity_table_1m,
    velocity_table_5m,
)

logger = logging.getLogger(__name__)

class TransactionRecord(faust.Record, serializer="json"):
    transaction_id: str
    tenant_id: str
    customer_id: str
    merchant_id: str
    amount: float
    currency: str
    timestamp: str
    status: str
    payment_method: str
    mcc: str
    shipping_address_hash: str
    device_fingerprint: str
    ip_address: str

transactions_topic = app.topic("transactions.raw", value_type=TransactionRecord)

redis_client = None

@app.task
async def setup_redis():
    global redis_client
    redis_client = RedisClient(str(settings.REDIS_URL))

@app.agent(transactions_topic)
async def process_transactions(stream):
    async for tx in stream:
        key = f"{tx.tenant_id}:{tx.customer_id}"

        # 1. Update velocity counters
        velocity_table_1m[key] += 1
        velocity_table_5m[key] += 1
        velocity_table_1h[key] += 1

        # 2. Update amount windows
        update_amount_window(tx.tenant_id, tx.customer_id, tx.amount)

        # 3. Write computed features to Redis
        velocity_stats = get_velocity(tx.tenant_id, tx.customer_id)
        amount_stats = get_amount_stats(tx.tenant_id, tx.customer_id)

        features = {
            "velocity_1m": float(velocity_stats["1m"]),
            "velocity_5m": float(velocity_stats["5m"]),
            "velocity_1h": float(velocity_stats["1h"]),
            "amount_mean_1h": float(amount_stats["mean"]),
            "amount_std_1h": float(amount_stats["stddev"]),
            "amount_p95_1h": float(amount_stats["p95"]),
            "amount_count_1h": float(amount_stats["count"]),
        }

        if redis_client:
            try:
                await redis_client.set_feature_vector(
                    customer_id=tx.customer_id,
                    tenant_id=UUID(tx.tenant_id),
                    features=features,
                    ttl=3600
                )
            except Exception as e:
                logger.error(f"Failed to write features to Redis for {key}: {e}")
