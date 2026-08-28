import logging
import neo4j
from neo4j import AsyncGraphDatabase

from src.streaming.app import app
from src.streaming.processors.transaction_processor import transactions_topic
from src.config import settings

logger = logging.getLogger(__name__)

neo4j_driver: neo4j.AsyncDriver | None = None

@app.task
async def setup_neo4j():
    global neo4j_driver
    password = settings.NEO4J_PASSWORD.get_secret_value() if hasattr(settings.NEO4J_PASSWORD, "get_secret_value") else settings.NEO4J_PASSWORD
    neo4j_driver = AsyncGraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(settings.NEO4J_USER, password)
    )


async def update_neo4j_batch(batch):
    if not neo4j_driver:
        return
        
    query = """
    UNWIND $events AS event
    MERGE (b:Buyer {id: event.customer_id, tenant_id: event.tenant_id})
    MERGE (s:Seller {id: event.merchant_id})
    MERGE (a:Address {hash: event.shipping_address_hash})
    MERGE (d:Device {fingerprint: event.device_fingerprint})
    MERGE (p:PaymentInstrument {token: event.payment_method})
    
    CREATE (b)-[:BOUGHT_FROM {amount: event.amount, timestamp: event.timestamp}]->(s)
    MERGE (b)-[:USES]->(d)
    MERGE (b)-[:SHIPS_TO]->(a)
    MERGE (b)-[:PAYS_WITH]->(p)
    """
    
    # Prepare batch data
    events_data = []
    for tx in batch:
        events_data.append({
            "customer_id": tx.customer_id,
            "tenant_id": tx.tenant_id,
            "merchant_id": tx.merchant_id,
            "shipping_address_hash": tx.shipping_address_hash,
            "device_fingerprint": tx.device_fingerprint,
            "payment_method": tx.payment_method,
            "amount": tx.amount,
            "timestamp": tx.timestamp,
        })
        
    async with neo4j_driver.session() as session:
        try:
            await session.run(query, events=events_data)
        except Exception as e:
            logger.error(f"Failed to execute Neo4j batch update: {e}")

@app.agent(transactions_topic)
async def process_graph_updates(stream):
    async for batch in stream.take(100, within=5.0):
        if batch:
            await update_neo4j_batch(batch)
