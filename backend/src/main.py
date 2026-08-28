"""FastAPI application entrypoint for AI Risk Manager."""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.v1 import (
    chargebacks_router,
    returns_router,
    fraud_router,
    cases_router,
    metrics_router,
    health_router,
)
from src.api.middleware.request_id import RequestIDMiddleware
from src.api.middleware.metrics import PrometheusMiddleware
from src.config import settings
from src.integrations.kafka_producer import TypedKafkaProducer
from src.integrations.langfuse_client import LangfuseTracer
from src.integrations.llm_client import GeminiLLMClient
from src.integrations.minio_client import ObjectStoreClient
from src.integrations.qdrant_client import QdrantVectorStore
from src.integrations.redis_client import RedisClient
from src.integrations.otel_setup import setup_opentelemetry
from src.db.session import async_engine

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ai_risk_manager")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application startup and shutdown lifecycle management."""
    logger.info(
        "Starting AI Risk Manager backend [env=%s, debug=%s]",
        settings.ENVIRONMENT,
        settings.DEBUG,
    )

    # Initialize Integration Clients
    app.state.redis = RedisClient(settings.REDIS_URL)
    app.state.kafka = TypedKafkaProducer(settings.KAFKA_BOOTSTRAP_SERVERS)
    app.state.qdrant = QdrantVectorStore(settings.QDRANT_URL)
    app.state.llm = GeminiLLMClient(
        settings.GEMINI_API_KEY.get_secret_value() if settings.GEMINI_API_KEY else "mock_key"
    )
    app.state.langfuse = LangfuseTracer(
        settings.LANGFUSE_PUBLIC_KEY,
        settings.LANGFUSE_SECRET_KEY.get_secret_value()
        if settings.LANGFUSE_SECRET_KEY
        else "mock_secret",
        settings.LANGFUSE_HOST,
    )
    app.state.minio = ObjectStoreClient(
        f"http://{settings.MINIO_ENDPOINT}",
        settings.MINIO_ACCESS_KEY,
        settings.MINIO_SECRET_KEY.get_secret_value()
        if settings.MINIO_SECRET_KEY
        else "mock_secret",
    )

    # Start and ensure connections
    await app.state.kafka.start()
    await app.state.qdrant.ensure_collection()
    await app.state.minio.ensure_buckets()

    yield

    logger.info("Shutting down AI Risk Manager backend.")
    await app.state.kafka.stop()
    await app.state.redis.close()
    await app.state.qdrant.close()
    app.state.langfuse.flush()


def create_app() -> FastAPI:
    """Factory function for FastAPI application instance."""
    app = FastAPI(
        title="AI Risk Manager API",
        description="Production-grade AI Risk Management system for fraud, returns, and chargeback defense in BFSI.",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.ENVIRONMENT == "dev" else ["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount middlewares
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(PrometheusMiddleware)

    # Mount base health routes
    app.include_router(health_router, prefix="")
    
    # Mount API v1 routes
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(chargebacks_router, prefix="/api/v1")
    app.include_router(returns_router, prefix="/api/v1")
    app.include_router(fraud_router, prefix="/api/v1")
    app.include_router(cases_router, prefix="/api/v1")
    app.include_router(metrics_router, prefix="/api/v1")

    # Initialize OpenTelemetry
    setup_opentelemetry(app, async_engine)

    return app


app = create_app()
