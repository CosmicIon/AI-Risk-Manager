import pytest
import uuid
from datetime import datetime, UTC
from decimal import Decimal
from src.integrations.kafka_producer import TypedKafkaProducer
from src.config import settings
from src.core.events import TransactionEvent
from src.core.exceptions import SchemaValidationError

@pytest.mark.asyncio
async def test_kafka_producer():
    producer = TypedKafkaProducer(settings.KAFKA_BOOTSTRAP_SERVERS)
    await producer.start()
    
    is_healthy = await producer.health_check()
    assert is_healthy, "Kafka health check failed"
    
    event = TransactionEvent(
        event_id=str(uuid.uuid4()),
        transaction_id="tx_123",
        tenant_id=uuid.uuid4(),
        amount=Decimal("100.00"),
        currency="USD",
        customer_id="cust_1",
        merchant_id="merch_1",
        merchant_category_code="1234",
        payment_method="cc",
        timestamp=datetime.now(UTC),
    )
    
    # Should succeed
    await producer.send_event("transactions.raw", event)
    
    # Should fail validation
    with pytest.raises(SchemaValidationError):
        await producer.send_event("transactions.raw", "not an event") # type: ignore
        
    await producer.stop()
