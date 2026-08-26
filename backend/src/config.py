"""Application configuration settings based on Pydantic Settings."""

from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Production-grade configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # Application & Environment
    ENVIRONMENT: Literal["dev", "staging", "prod"] = "dev"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Security & JWT
    JWT_SECRET: SecretStr = SecretStr("super_secret_jwt_signing_key_change_in_production_min_32_chars")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480

    # Database (PostgreSQL 16)
    DATABASE_URL: str = "postgresql+asyncpg://riskmanager:dev_password@localhost:5432/riskmanager"
    DATABASE_SYNC_URL: str = "postgresql://riskmanager:dev_password@localhost:5432/riskmanager"

    # Redis 7
    REDIS_URL: str = "redis://localhost:6379/0"

    # Apache Kafka
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:9092"
    KAFKA_CONSUMER_GROUP: str = "ai-risk-manager-backend"

    # Vector DB (Qdrant)
    QDRANT_URL: str = "http://localhost:6333"
    QDRANT_API_KEY: str | None = None

    # Neo4j Entity Graph
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: SecretStr = SecretStr("dev_password")

    # MinIO / Object Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: SecretStr = SecretStr("minioadmin")
    MINIO_SECURE: bool = False
    MINIO_REGION: str = "ap-south-1"
    S3_BUCKET_MODELS: str = "models"
    S3_BUCKET_HOLDOUT: str = "holdout"
    S3_BUCKET_EVIDENCE: str = "evidence"
    S3_BUCKET_REPORTS: str = "reports"

    # Gemini & LLM Orchestration
    GEMINI_API_KEY: SecretStr = SecretStr("placeholder_key")
    GEMINI_MODEL: str = "gemini-2.5-flash"

    # Langfuse
    LANGFUSE_PUBLIC_KEY: str = "pk-lf-local-placeholder"
    LANGFUSE_SECRET_KEY: SecretStr = SecretStr("sk-lf-local-placeholder")
    LANGFUSE_HOST: str = "http://localhost:3001"

    # Tracing & Telemetry
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://localhost:4317"
    OTEL_SERVICE_NAME: str = "ai-risk-manager-backend"


settings = Settings()
