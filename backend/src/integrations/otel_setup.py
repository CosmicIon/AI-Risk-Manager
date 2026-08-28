import logging
import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.semconv.resource import ResourceAttributes

logger = logging.getLogger(__name__)


def setup_opentelemetry(app: FastAPI, engine=None):
    """
    Configure OpenTelemetry distributed tracing and instrument libraries.
    """
    otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")

    if not otel_endpoint:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set. OpenTelemetry tracing is disabled.")
        return

    # Set up TracerProvider
    resource = Resource.create(
        {
            ResourceAttributes.SERVICE_NAME: "ai-risk-manager-backend",
            ResourceAttributes.SERVICE_VERSION: "1.0.0",
        }
    )

    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)

    # Set up Exporter (OTLP gRPC)
    try:
        otlp_exporter = OTLPSpanExporter(endpoint=otel_endpoint, insecure=True)
        span_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(span_processor)
        logger.info(f"Configured OTLP exporter to {otel_endpoint}")
    except Exception as e:
        logger.error(f"Failed to configure OTLP exporter: {e}")

    # Auto-instrumentations
    try:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("FastAPI instrumented with OpenTelemetry")
    except Exception as e:
        logger.warning(f"Could not instrument FastAPI: {e}")

    if engine:
        try:
            # For async engines, we instrument the underlying sync_engine
            sync_engine = getattr(engine, "sync_engine", engine)
            SQLAlchemyInstrumentor().instrument(engine=sync_engine)
            logger.info("SQLAlchemy instrumented with OpenTelemetry")
        except Exception as e:
            logger.warning(f"Could not instrument SQLAlchemy: {e}")

    try:
        HTTPXClientInstrumentor().instrument()
        logger.info("HTTPX instrumented with OpenTelemetry")
    except Exception as e:
        logger.warning(f"Could not instrument HTTPX: {e}")
