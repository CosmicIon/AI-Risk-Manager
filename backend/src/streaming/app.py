import faust
from src.config import settings

# Initialize Faust app
app = faust.App(
    "risk-manager",
    broker=str(settings.KAFKA_BOOTSTRAP_SERVERS),
    store="rocksdb://",
    topic_partitions=8,
)

@app.page("/health")
async def health(web, request):
    return web.json({"status": "ok"})

# Import agents to register them with the app
import src.streaming.processors.transaction_processor  # noqa
import src.streaming.processors.anomaly_processor  # noqa
import src.streaming.processors.graph_updater  # noqa
