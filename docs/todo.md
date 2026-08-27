# AI Risk Manager — Implementation Roadmap

> **Usage:** This file is the single source of truth for implementation sequencing.
> Every `- [x]` item is actionable. Mark `- [/]` when in progress, `- [x]` when complete.
> **No module may begin until the prior module's verification gate passes.**

---

## Module 0: Project Scaffolding & Development Environment

**Goal:** Establish a reproducible, containerized development environment with all infrastructure dependencies bootable via a single command.

### Key Files Created

- `pyproject.toml` (root workspace)
- `backend/pyproject.toml`
- `backend/src/__init__.py`
- `backend/src/main.py`
- `backend/src/config.py`
- `backend/tests/conftest.py`
- `dashboard/package.json`
- `dashboard/tsconfig.json`
- `dashboard/next.config.ts`
- `infra/docker/docker-compose.yml`
- `infra/docker/Dockerfile.backend`
- `infra/docker/Dockerfile.dashboard`
- `infra/docker/Dockerfile.streaming`
- `.env.example`
- `.gitignore`
- `Makefile`
- `.github/workflows/ci.yml`

### Implementation Checklist

- [x] **0.1 — Root workspace configuration**
  - [x] Create root `pyproject.toml` with workspace definition pointing to `backend/`
  - [x] Create `backend/pyproject.toml` with dependencies: `fastapi>=0.115`, `uvicorn[standard]`, `pydantic>=2.0`, `pydantic-settings`, `sqlalchemy[asyncio]>=2.0`, `asyncpg`, `alembic`, `redis[hiredis]>=5.0`, `aiokafka`, `celery[redis]>=5.3`, `onnxruntime>=1.17`, `lightgbm>=4.0`, `langgraph>=0.2`, `langchain-google-genai`, `qdrant-client>=1.9`, `shap>=0.45`, `scikit-learn>=1.4`, `great-expectations>=0.18`, `opentelemetry-api`, `opentelemetry-sdk`, `opentelemetry-instrumentation-fastapi`, `langfuse>=2.0`, `prometheus-client`, `httpx`, `python-multipart`, `python-jose[cryptography]`, `passlib[bcrypt]`, `boto3` (for MinIO/S3)
  - [x] Add dev dependencies: `pytest>=8.0`, `pytest-asyncio>=0.23`, `pytest-cov`, `httpx` (for `TestClient`), `factory-boy`, `faker`, `ruff`, `mypy`, `testcontainers[postgres,redis,kafka]`

- [x] **0.2 — FastAPI application skeleton**
  - [x] Create `backend/src/main.py`: instantiate `FastAPI(title="AI Risk Manager", version="0.1.0")`, include CORS middleware, mount health router
  - [x] Create `backend/src/config.py`: define `class Settings(BaseSettings)` with fields: `DATABASE_URL: str`, `REDIS_URL: str`, `KAFKA_BOOTSTRAP_SERVERS: str`, `QDRANT_URL: str`, `NEO4J_URI: str`, `NEO4J_USER: str`, `NEO4J_PASSWORD: SecretStr`, `GEMINI_API_KEY: SecretStr`, `LANGFUSE_PUBLIC_KEY: str`, `LANGFUSE_SECRET_KEY: SecretStr`, `MINIO_ENDPOINT: str`, `MINIO_ACCESS_KEY: str`, `MINIO_SECRET_KEY: SecretStr`, `JWT_SECRET: SecretStr`, `JWT_ALGORITHM: str = "HS256"`, `ENVIRONMENT: Literal["dev", "staging", "prod"] = "dev"`. Use `model_config = SettingsConfigDict(env_file=".env")`
  - [x] Create `backend/src/api/v1/health.py`: implement `GET /health` (returns `{"status": "ok"}`), `GET /readiness` (checks DB + Redis + Kafka connectivity, returns per-dependency status)

- [x] **0.3 — Docker Compose local stack**
  - [x] Create `infra/docker/docker-compose.yml` with services:
    - `postgres`: image `postgres:16-alpine`, port `5432`, volume `pgdata`, env `POSTGRES_DB=riskmanager`, `POSTGRES_USER=riskmanager`, `POSTGRES_PASSWORD=dev_password`, healthcheck `pg_isready`
    - `redis`: image `redis:7-alpine`, port `6379`, healthcheck `redis-cli ping`
    - `kafka`: image `bitnami/kafka:3.7` (KRaft mode), ports `9092:9092`, env `KAFKA_CFG_NODE_ID=0`, `KAFKA_CFG_PROCESS_ROLES=broker,controller`, `KAFKA_CFG_CONTROLLER_QUORUM_VOTERS=0@kafka:9093`, `KAFKA_CFG_LISTENERS=PLAINTEXT://:9092,CONTROLLER://:9093`, `KAFKA_CFG_AUTO_CREATE_TOPICS_ENABLE=true`
    - `qdrant`: image `qdrant/qdrant:v1.9.0`, port `6333`, volume `qdrant_data`
    - `neo4j`: image `neo4j:5-community`, ports `7474:7474`, `7687:7687`, env `NEO4J_AUTH=neo4j/dev_password`, `NEO4J_PLUGINS=["graph-data-science"]`
    - `minio`: image `minio/minio:latest`, command `server /data --console-address ":9001"`, ports `9000:9000`, `9001:9001`, env `MINIO_ROOT_USER=minioadmin`, `MINIO_ROOT_PASSWORD=minioadmin`
    - `langfuse`: image `langfuse/langfuse:2`, port `3001`, depends_on `postgres`, env pointing to the shared postgres
  - [x] Create `infra/docker/Dockerfile.backend`: multi-stage build — `python:3.12-slim` base, install `uv`, copy `pyproject.toml`, `uv sync --frozen`, copy `src/`, `CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]`
  - [x] Create `infra/docker/Dockerfile.dashboard`: multi-stage build — `node:22-alpine`, `npm ci`, `npm run build`, `CMD ["npm", "start"]`
  - [x] Create `infra/docker/Dockerfile.streaming`: based on `Dockerfile.backend`, `CMD ["faust", "-A", "src.streaming.app", "worker", "-l", "info"]`

- [x] **0.4 — Environment template and gitignore**
  - [x] Create `.env.example` with all `Settings` fields documented (placeholder values)
  - [x] Create `.gitignore`: Python (`__pycache__`, `*.pyc`, `.venv`, `dist/`), Node (`node_modules/`, `.next/`), IDE (`.vscode/`, `.idea/`), data (`data/holdout/`, `models/*/v*/`), secrets (`.env`), Docker (`pgdata`, `qdrant_data`)

- [x] **0.5 — Makefile with development commands**
  - [x] `make up`: `docker compose -f infra/docker/docker-compose.yml up -d`
  - [x] `make down`: `docker compose -f infra/docker/docker-compose.yml down -v`
  - [x] `make backend-dev`: `cd backend && uvicorn src.main:app --reload --port 8000`
  - [x] `make dashboard-dev`: `cd dashboard && npm run dev`
  - [x] `make test`: `cd backend && pytest tests/ -v --cov=src`
  - [x] `make lint`: `cd backend && ruff check src/ tests/ && mypy src/`
  - [x] `make migrate`: `cd backend && alembic upgrade head`
  - [x] `make seed`: `cd backend && python scripts/seed_db.py`

- [x] **0.6 — CI pipeline (GitHub Actions)**
  - [x] Create `.github/workflows/ci.yml`: trigger on push/PR to `main`, jobs:
    - `lint`: run `ruff check`, `mypy`
    - `test-backend`: spin up postgres + redis via `services`, run `pytest tests/unit/ -v --cov --cov-fail-under=80`
    - `test-dashboard`: `npm ci && npm run lint && npm run build`

- [x] **0.7 — Next.js dashboard scaffolding**
  - [x] Initialize Next.js 15 in `dashboard/` with App Router, TypeScript, ESLint, Vanilla CSS design tokens
  - [x] Create `dashboard/src/app/globals.css`, `dashboard/src/app/layout.tsx`, and `dashboard/src/app/page.tsx`

### Acceptance Criteria

- [x] `make up` starts all 7 infrastructure containers with passing health checks
- [x] `curl http://localhost:8000/health` returns `{"status": "ok"}`
- [x] `curl http://localhost:8000/readiness` returns status for each dependency
- [x] `make test` runs (even if no tests yet) without import errors
- [x] `make lint` passes with zero errors
- [x] Dashboard accessible at `http://localhost:3000`
- [x] CI pipeline runs green on push

### Verification Gate

```bash
# All must pass before proceeding to Module 1
docker compose -f infra/docker/docker-compose.yml ps  # all 7 services "healthy"
curl -s http://localhost:8000/health | python -c "import sys,json; d=json.load(sys.stdin); assert d['status']=='ok'"
curl -s http://localhost:8000/readiness | python -c "import sys,json; d=json.load(sys.stdin); assert all(v=='ok' for v in d.values())"
cd backend && pytest tests/ -v --tb=short
cd backend && ruff check src/ && mypy src/
cd dashboard && npm run build
```

**Sign-off:** All 7 containers healthy, `/health` + `/readiness` pass, linter clean, dashboard builds.

---

## Module 1: Data Contracts, Enums & Kafka Event Schemas

**Goal:** Define every Pydantic schema, enum, domain exception, and Avro event schema that will flow through the system — establishing the typed data contracts before any business logic.

### Key Files Created / Modified

- `backend/src/core/enums.py`
- `backend/src/core/exceptions.py`
- `backend/src/core/schemas/chargeback.py`
- `backend/src/core/schemas/return_request.py`
- `backend/src/core/schemas/fraud_alert.py`
- `backend/src/core/schemas/case.py`
- `backend/src/core/schemas/evaluation.py`
- `backend/src/core/events.py`
- `data/schemas/transaction.avsc`
- `data/schemas/chargeback_notification.avsc`
- `data/schemas/return_request.avsc`
- `backend/tests/unit/test_schemas.py`

### Implementation Checklist

- [x] **1.1 — Enums (`backend/src/core/enums.py`)**
  - [x] `CardNetwork(str, Enum)`: `VISA`, `MASTERCARD`, `RUPAY`, `AMEX`
  - [x] `ReasonCode(str, Enum)`: At minimum — `FRAUD_CARD_NOT_PRESENT = "10.4"`, `MERCHANDISE_NOT_RECEIVED = "13.1"`, `NOT_AS_DESCRIBED = "13.3"`, `DUPLICATE_PROCESSING = "12.2"`, `CANCELLED_RECURRING = "13.7"` (Visa codes), plus Mastercard equivalents `UNAUTHORIZED_TRANSACTION = "4837"`, `CARDHOLDER_DISPUTE = "4853"`. Add `@classmethod from_network_code(cls, network: CardNetwork, raw_code: str) -> ReasonCode` mapper
  - [x] `RiskTier(str, Enum)`: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
  - [x] `CaseStatus(str, Enum)`: `NEW`, `EVIDENCE_GATHERING`, `DRAFT_READY`, `IN_REVIEW`, `APPROVED`, `SUBMITTED`, `WON`, `LOST`, `EXPIRED`, `ACCEPTED_LOSS`
  - [x] `CaseSource(str, Enum)`: `CHARGEBACK`, `RETURN`, `FRAUD_ALERT`, `ABUSE_RING`
  - [x] `SpikeClassification(str, Enum)`: `ORGANIC_SPIKE`, `ATTACK`, `UNCERTAIN`
  - [x] `AlertSeverity(str, Enum)`: `INFO`, `WARNING`, `CRITICAL`, `EMERGENCY`
  - [x] `NotificationChannel(str, Enum)`: `EMAIL`, `SLACK`, `PAGERDUTY`, `SMS`

- [x] **1.2 — Domain exceptions (`backend/src/core/exceptions.py`)**
  - [x] `RiskManagerError(Exception)`: base exception with `message: str`, `error_code: str`
  - [x] `SchemaValidationError(RiskManagerError)`: raised on Pydantic validation failures at service boundaries
  - [x] `CaseNotFoundError(RiskManagerError)`: raised when case ID lookup fails
  - [x] `DuplicateIngestionError(RiskManagerError)`: raised on duplicate chargeback (idempotency violation)
  - [x] `ModelInferenceError(RiskManagerError)`: raised when ONNX Runtime inference fails
  - [x] `EvidenceRetrievalError(RiskManagerError)`: raised when an agent tool fails to fetch evidence
  - [x] `LLMResponseError(RiskManagerError)`: raised when LLM returns malformed/unparseable output
  - [x] `FeatureStoreUnavailableError(RiskManagerError)`: raised when Redis feature cache is unreachable
  - [x] `DeadlineExceededError(RiskManagerError)`: raised when chargeback representment deadline has passed

- [x] **1.3 — Chargeback schemas (`backend/src/core/schemas/chargeback.py`)**
  - [x] `ChargebackNotification(BaseModel)`: fields — `notification_id: str`, `network: CardNetwork`, `arn: str` (Acquirer Reference Number), `raw_reason_code: str`, `reason_code: ReasonCode`, `transaction_id: str`, `transaction_date: datetime`, `transaction_amount: Decimal`, `currency: str = "INR"`, `cardholder_name: str | None`, `merchant_id: str`, `tenant_id: UUID`, `received_at: datetime`, `deadline: datetime`. Add `@model_validator(mode="after")` to compute `deadline` from `received_at` + network-specific days (Visa: 30, Mastercard: 45). Add `@computed_field idempotency_key` returning `f"{network.value}:{arn}"`
  - [x] `EvidenceItem(BaseModel)`: `evidence_type: Literal["delivery_proof", "avs_match", "3ds_log", "customer_communication", "order_confirmation", "refund_receipt", "ip_geolocation"]`, `source: str`, `content: str | None`, `file_url: str | None`, `retrieved_at: datetime`, `confidence: float` (0.0-1.0)
  - [x] `EvidenceBundle(BaseModel)`: `case_id: UUID`, `items: list[EvidenceItem]`, `completeness_score: float` (fraction of required evidence retrieved), `missing_evidence: list[str]`
  - [x] `RepresentmentDraft(BaseModel)`: `case_id: UUID`, `narrative: str`, `evidence_summary: str`, `network_template_version: str`, `win_probability: float`, `recommendation: Literal["respond", "accept_loss"]`, `generated_at: datetime`, `llm_model_used: str`, `prompt_version: str`
  - [x] `ChargebackIngestRequest(BaseModel)`: wraps raw webhook payload with `raw_payload: dict[str, Any]`, `source_ip: str | None`, `webhook_signature: str | None`
  - [x] `ChargebackIngestResponse(BaseModel)`: `case_id: UUID`, `status: CaseStatus`, `deadline: datetime`, `message: str`

- [x] **1.4 — Return request schemas (`backend/src/core/schemas/return_request.py`)**
  - [x] `ReturnScoreRequest(BaseModel)`: `request_id: str`, `tenant_id: UUID`, `customer_id: str`, `order_id: str`, `order_amount: Decimal`, `return_amount: Decimal`, `return_reason: str`, `order_date: datetime`, `return_initiated_at: datetime`, `product_category: str`, `device_fingerprint: str | None`, `ip_address: str | None`. Add `@field_validator("return_amount")` ensuring `return_amount <= order_amount`
  - [x] `FeatureVector(BaseModel)`: `customer_id: str`, `features: dict[str, float]`, `computed_at: datetime`, `staleness_seconds: float`, `is_degraded: bool = False` (true when feature store was partially unavailable)
  - [x] `ReturnScoreResponse(BaseModel)`: `request_id: str`, `risk_score: int` (0-100, `@field_validator` clamping), `risk_tier: RiskTier`, `decision: Literal["auto_approve", "manual_review", "auto_deny"]`, `explanation: str`, `top_features: list[dict[str, float]]` (top-5 SHAP values), `model_version: str`, `inference_latency_ms: float`, `scored_at: datetime`
  - [x] `PolicyConfig(BaseModel)`: `tenant_id: UUID`, `low_threshold: int = 25`, `medium_threshold: int = 50`, `high_threshold: int = 75`, `auto_deny_enabled: bool = False`, `high_value_customer_override: bool = True` (if true, high-LTV customers with HIGH tier go to manual_review instead of auto_deny)

- [x] **1.5 — Fraud alert schemas (`backend/src/core/schemas/fraud_alert.py`)**
  - [x] `AnomalyAlert(BaseModel)`: `alert_id: UUID`, `tenant_id: UUID`, `detected_at: datetime`, `severity: AlertSeverity`, `spike_classification: SpikeClassification`, `affected_segment: str` (e.g., "MCC:5411, city:Mumbai"), `baseline_tps: float`, `current_tps: float`, `deviation_factor: float`, `window_seconds: int`, `is_calendar_adjusted: bool`
  - [x] `FraudSpikeDetail(BaseModel)`: `alert_id: UUID`, `transaction_ids: list[str]`, `geographic_spread: dict[str, int]`, `amount_distribution: dict[str, float]` (mean, median, stddev, p95), `velocity_profile: list[dict[str, Any]]` (per-second counts over the anomaly window)

- [x] **1.6 — Case management schemas (`backend/src/core/schemas/case.py`)**
  - [x] `CaseCreate(BaseModel)`: `tenant_id: UUID`, `source: CaseSource`, `source_id: str` (e.g., chargeback ARN, return request_id), `priority: int = 0` (higher = more urgent), `metadata: dict[str, Any] = {}`
  - [x] `Case(BaseModel)`: `case_id: UUID`, `tenant_id: UUID`, `source: CaseSource`, `source_id: str`, `status: CaseStatus`, `assigned_to: UUID | None`, `priority: int`, `created_at: datetime`, `updated_at: datetime`, `deadline: datetime | None`, `resolution: str | None`, `metadata: dict[str, Any]`
  - [x] `CaseUpdate(BaseModel)`: `status: CaseStatus | None`, `assigned_to: UUID | None`, `resolution: str | None`, `metadata: dict[str, Any] | None`
  - [x] `AuditLogEntry(BaseModel)`: `entry_id: UUID`, `case_id: UUID`, `actor_id: UUID`, `action: str`, `old_value: dict[str, Any] | None`, `new_value: dict[str, Any] | None`, `timestamp: datetime`, `ip_address: str | None`

- [x] **1.7 — Evaluation schemas (`backend/src/core/schemas/evaluation.py`)**
  - [x] `CostWeightedMetrics(BaseModel)`: `precision: float`, `recall: float`, `f1: float`, `auc_roc: float`, `fp_count: int`, `fn_count: int`, `tp_count: int`, `tn_count: int`, `fp_cost_per_unit: Decimal`, `fn_cost_per_unit: Decimal`, `total_fp_cost: Decimal`, `total_fn_cost: Decimal`, `cost_weighted_loss: float` (formula: `(fp_cost_per_unit * fp_count + fn_cost_per_unit * fn_count) / total_samples`)
  - [x] `EvaluationReport(BaseModel)`: `report_id: UUID`, `model_name: str`, `model_version: str`, `holdout_set_version: str`, `holdout_set_hash: str` (SHA-256), `metrics: CostWeightedMetrics`, `threshold_used: float`, `champion_model_version: str | None`, `is_improvement: bool | None` (true if cost_weighted_loss is lower than champion), `evaluated_at: datetime`, `report_url: str` (S3 path to full report)
  - [x] `DriftReport(BaseModel)`: `feature_name: str`, `psi_value: float`, `kl_divergence: float`, `is_drifted: bool` (PSI > 0.1), `requires_retrain: bool` (PSI > 0.2), `reference_distribution: dict[str, float]`, `current_distribution: dict[str, float]`, `computed_at: datetime`

- [x] **1.8 — Kafka event schemas (`backend/src/core/events.py`)**
  - [x] `TransactionEvent(BaseModel)`: `event_id: str`, `tenant_id: UUID`, `transaction_id: str`, `timestamp: datetime`, `amount: Decimal`, `currency: str`, `merchant_id: str`, `merchant_category_code: str`, `customer_id: str`, `payment_method: str`, `device_fingerprint: str | None`, `ip_address: str | None`, `city: str | None`, `country: str = "IN"`
  - [x] `ChargebackEvent(BaseModel)`: wraps `ChargebackNotification` with `event_type: Literal["chargeback.received", "chargeback.evidence_ready", "chargeback.submitted", "chargeback.resolved"]`
  - [x] `ReturnEvent(BaseModel)`: wraps `ReturnScoreRequest` + `ReturnScoreResponse` with `event_type: Literal["return.scored", "return.decision_overridden"]`
  - [x] `AlertEvent(BaseModel)`: wraps `AnomalyAlert` with `event_type: Literal["alert.fraud_spike", "alert.abuse_ring"]`
  - [x] Define `TOPIC_MAP: dict[str, type[BaseModel]]` mapping topic names to event schemas: `{"transactions.raw": TransactionEvent, "chargebacks.incoming": ChargebackEvent, ...}`

- [x] **1.9 — Avro schemas for Kafka topics**
  - [x] Create `data/schemas/transaction.avsc`: Avro schema mirroring `TransactionEvent` fields with `logicalType` annotations (e.g., `timestamp-millis` for datetimes, `decimal` with precision/scale for amounts)
  - [x] Create `data/schemas/chargeback_notification.avsc`: Avro schema mirroring `ChargebackNotification`
  - [x] Create `data/schemas/return_request.avsc`: Avro schema mirroring `ReturnScoreRequest`

### Acceptance Criteria

- [x] All Pydantic models instantiate correctly with valid data
- [x] All Pydantic models raise `ValidationError` with invalid data (e.g., `return_amount > order_amount`, `risk_score` outside 0-100, missing required fields)
- [x] `ChargebackNotification.deadline` auto-computed correctly: Visa → +30 days, Mastercard → +45 days
- [x] `ChargebackNotification.idempotency_key` is deterministic for the same network + ARN
- [x] All enums are JSON-serializable (string values)
- [x] Avro schemas are valid and parseable by `fastavro`
- [x] `CostWeightedMetrics.cost_weighted_loss` computation is verified with known inputs

### Verification Gate

```bash
cd backend && pytest tests/unit/test_schemas.py -v --tb=short
# Expected: 30+ test cases, all passing
# Specific assertions verified:
#   - ChargebackNotification deadline computation (Visa 30d, MC 45d)
#   - ReturnScoreRequest validator rejects return_amount > order_amount
#   - ReturnScoreResponse clamps risk_score to [0, 100]
#   - CostWeightedMetrics computes cost_weighted_loss correctly
#   - All enums round-trip through JSON serialization
#   - Avro schemas parse without errors
```

**Sign-off:** All schema tests pass. Every data contract is typed, validated, and tested.

---

## Module 2: Database Layer, Migrations & Persistence

**Goal:** Build the full SQLAlchemy ORM layer, Alembic migration pipeline, PostgreSQL RLS for multi-tenancy, and repository pattern for data access — ready for all four risk modules.

### Key Files Created / Modified

- `backend/src/db/__init__.py`
- `backend/src/db/session.py`
- `backend/src/db/models/tenant.py`
- `backend/src/db/models/user.py`
- `backend/src/db/models/case.py`
- `backend/src/db/models/chargeback.py`
- `backend/src/db/models/evaluation_run.py`
- `backend/src/db/models/audit_log.py`
- `backend/src/db/repositories/case_repo.py`
- `backend/src/db/repositories/chargeback_repo.py`
- `backend/src/db/repositories/evaluation_repo.py`
- `backend/alembic/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/001_initial_schema.py`
- `backend/scripts/seed_db.py`

### Implementation Checklist

- [x] **2.1 — Async session factory (`backend/src/db/session.py`)**
  - [x] Create `async_engine` using `create_async_engine(settings.DATABASE_URL, pool_size=20, max_overflow=10, pool_pre_ping=True)`
  - [x] Create `AsyncSessionLocal` using `async_sessionmaker(async_engine, expire_on_commit=False)`
  - [x] Implement `async def get_db_session() -> AsyncGenerator[AsyncSession, None]` as a FastAPI dependency
  - [x] Implement `async def get_db_session_with_tenant(tenant_id: UUID)` that sets `SET app.current_tenant = '{tenant_id}'` for RLS

- [x] **2.2 — ORM models**
  - [x] `Tenant` (`backend/src/db/models/tenant.py`): `id: UUID (PK)`, `name: str`, `api_key_hash: str`, `fp_cost_per_unit: Decimal = 500`, `fn_cost_per_unit: Decimal = 2000`, `policy_config: JSON` (stores `PolicyConfig` as JSONB), `created_at: DateTime`, `is_active: bool = True`
  - [x] `User` (`backend/src/db/models/user.py`): `id: UUID (PK)`, `tenant_id: UUID (FK -> Tenant)`, `email: str (unique)`, `password_hash: str`, `role: str` (enum: `admin`, `analyst`, `ml_engineer`, `compliance`), `created_at: DateTime`, `is_active: bool = True`
  - [x] `Case` (`backend/src/db/models/case.py`): `id: UUID (PK)`, `tenant_id: UUID (FK -> Tenant)`, `source: str (CaseSource)`, `source_id: str`, `status: str (CaseStatus)`, `assigned_to: UUID (FK -> User, nullable)`, `priority: int`, `deadline: DateTime (nullable)`, `resolution: str (nullable)`, `metadata: JSON`, `created_at: DateTime`, `updated_at: DateTime`. Index on `(tenant_id, status)`, `(tenant_id, deadline)`. Unique constraint on `(tenant_id, source, source_id)` for idempotency
  - [x] `ChargebackRecord` (`backend/src/db/models/chargeback.py`): `id: UUID (PK)`, `case_id: UUID (FK -> Case)`, `tenant_id: UUID (FK -> Tenant)`, `network: str`, `arn: str`, `reason_code: str`, `transaction_id: str`, `transaction_date: DateTime`, `transaction_amount: Decimal`, `evidence_bundle: JSON (nullable)`, `representment_draft: JSON (nullable)`, `win_probability: Float (nullable)`, `outcome: str (nullable)` (won/lost), `submitted_at: DateTime (nullable)`, `resolved_at: DateTime (nullable)`. Index on `(tenant_id, arn)` unique
  - [x] `EvaluationRun` (`backend/src/db/models/evaluation_run.py`): `id: UUID (PK)`, `model_name: str`, `model_version: str`, `holdout_set_version: str`, `holdout_set_hash: str`, `metrics: JSON` (stores `CostWeightedMetrics`), `threshold: Float`, `is_champion: bool = False`, `report_url: str`, `evaluated_at: DateTime`
  - [x] `AuditLog` (`backend/src/db/models/audit_log.py`): `id: UUID (PK)`, `tenant_id: UUID (FK -> Tenant)`, `case_id: UUID (FK -> Case, nullable)`, `actor_id: UUID (FK -> User)`, `action: str`, `old_value: JSON (nullable)`, `new_value: JSON (nullable)`, `timestamp: DateTime (server_default=func.now())`, `ip_address: str (nullable)`. Partitioned by month on `timestamp` for retention compliance

- [x] **2.3 — Alembic migration setup**
  - [x] Create `backend/alembic/alembic.ini` pointing to `backend/alembic/`
  - [x] Create `backend/alembic/env.py` with async engine support, importing all ORM models for autogenerate
  - [x] Create initial migration `001_initial_schema.py`:
    - All tables above
    - RLS policy: `CREATE POLICY tenant_isolation ON cases USING (tenant_id = current_setting('app.current_tenant')::uuid)` for tables: `cases`, `chargeback_records`, `audit_logs`
    - Enable RLS: `ALTER TABLE cases ENABLE ROW LEVEL SECURITY`
    - Partial index: `CREATE INDEX idx_cases_open ON cases(tenant_id, deadline) WHERE status NOT IN ('WON', 'LOST', 'EXPIRED', 'ACCEPTED_LOSS')`
    - Partition `audit_logs` by range on `timestamp` (monthly)

- [x] **2.4 — Repository layer**
  - [x] `CaseRepository` (`backend/src/db/repositories/case_repo.py`):
    - `async def create(session, case: CaseCreate) -> Case`: insert with conflict check on `(tenant_id, source, source_id)`, raise `DuplicateIngestionError` on conflict
    - `async def get_by_id(session, case_id: UUID, tenant_id: UUID) -> Case | None`
    - `async def list_by_status(session, tenant_id: UUID, status: CaseStatus, limit: int = 50, offset: int = 0) -> list[Case]`
    - `async def list_approaching_deadline(session, tenant_id: UUID, within_hours: int = 48) -> list[Case]`: returns cases with `deadline < now() + interval '{within_hours} hours'` and status not terminal
    - `async def update(session, case_id: UUID, tenant_id: UUID, update: CaseUpdate) -> Case`: writes audit log entry on every status change
  - [x] `ChargebackRepository` (`backend/src/db/repositories/chargeback_repo.py`):
    - `async def create(session, record: ChargebackRecord) -> ChargebackRecord`
    - `async def get_by_arn(session, tenant_id: UUID, arn: str) -> ChargebackRecord | None`
    - `async def update_evidence(session, case_id: UUID, evidence_bundle: dict) -> ChargebackRecord`
    - `async def update_outcome(session, case_id: UUID, outcome: str, resolved_at: datetime) -> ChargebackRecord`
    - `async def get_win_rate(session, tenant_id: UUID, window_days: int = 90) -> dict`: returns `{"total": int, "won": int, "lost": int, "win_rate": float}`
  - [x] `EvaluationRepository` (`backend/src/db/repositories/evaluation_repo.py`):
    - `async def create(session, run: EvaluationRun) -> EvaluationRun`
    - `async def get_champion(session, model_name: str) -> EvaluationRun | None`
    - `async def promote_to_champion(session, run_id: UUID) -> EvaluationRun`
    - `async def list_runs(session, model_name: str, limit: int = 20) -> list[EvaluationRun]`

- [x] **2.5 — Database seeding script (`backend/scripts/seed_db.py`)**
  - [x] Create a test tenant with `id = UUID("00000000-0000-0000-0000-000000000001")`
  - [x] Create 3 test users (admin, analyst, ml_engineer) for the test tenant
  - [x] Create 10 sample cases across all 4 case sources with varying statuses
  - [x] Create 5 sample chargeback records with evidence bundles

### Acceptance Criteria

- [x] `alembic upgrade head` runs without errors on a clean database
- [x] `alembic downgrade base` fully reverses all migrations
- [x] RLS policy prevents cross-tenant data access when `app.current_tenant` is set
- [x] `CaseRepository.create` raises `DuplicateIngestionError` on duplicate `(tenant_id, source, source_id)`
- [x] `CaseRepository.update` writes an audit log entry on every status change
- [x] `ChargebackRepository.get_win_rate` returns correct statistics
- [x] Seeding script creates all expected records

### Verification Gate

```bash
# Start postgres
make up
# Run migrations
cd backend && alembic upgrade head
# Verify tables exist
cd backend && python -c "from src.db.models import *; print('All models imported')"
# Run seed
cd backend && python scripts/seed_db.py
# Run repository tests
cd backend && pytest tests/unit/test_repositories.py -v --tb=short
# Verify RLS
cd backend && pytest tests/integration/test_rls_isolation.py -v
# Expected: All CRUD operations succeed, RLS blocks cross-tenant access, audit logs written
```

**Sign-off:** Migrations apply cleanly, RLS verified, all repository tests pass with correct audit trails.

---

## Module 3: Integration Clients & Infrastructure Connectors

**Goal:** Build typed, resilient client wrappers for every external system (Redis, Kafka, Qdrant, Neo4j, MinIO, LLM, Langfuse) with connection pooling, health checks, retry logic, and circuit breakers.

### Key Files Created / Modified

- `backend/src/integrations/__init__.py`
- `backend/src/integrations/redis_client.py`
- `backend/src/integrations/kafka_producer.py`
- `backend/src/integrations/qdrant_client.py`
- `backend/src/integrations/llm_client.py`
- `backend/src/integrations/langfuse_client.py`
- `backend/src/integrations/minio_client.py`
- `backend/src/api/deps.py`

### Implementation Checklist

- [x] **3.1 — Redis client (`backend/src/integrations/redis_client.py`)**
  - [x] `class RedisClient`: wraps `redis.asyncio.Redis` connection pool
  - [x] `async def get_feature_vector(customer_id: str, tenant_id: UUID) -> dict[str, float] | None`: fetch from key `features:{tenant_id}:{customer_id}`, deserialize JSON
  - [x] `async def set_feature_vector(customer_id: str, tenant_id: UUID, features: dict, ttl: int = 3600)`
  - [x] `async def increment_counter(key: str, window_seconds: int) -> int`: for rate limiting, uses `INCR` + `EXPIRE`
  - [x] `async def check_rate_limit(identifier: str, limit: int, window: int) -> tuple[bool, int]`: returns (is_allowed, remaining)
  - [x] `async def health_check() -> bool`: `PING`
  - [x] Connection pool config: `max_connections=50`, `decode_responses=True`, `socket_timeout=2.0`, `retry_on_timeout=True`

- [x] **3.2 — Kafka producer (`backend/src/integrations/kafka_producer.py`)**
  - [x] `class TypedKafkaProducer`: wraps `aiokafka.AIOKafkaProducer`
  - [x] `async def send_event(topic: str, event: BaseModel, key: str | None = None)`: serialize event to JSON bytes, send with optional partition key. Validate event type against `TOPIC_MAP` from `core/events.py` — raise `SchemaValidationError` if event type doesn't match topic
  - [x] `async def send_batch(topic: str, events: list[BaseModel], key_fn: Callable)`: batch send with per-event keys
  - [x] Retry config: `retries=3`, `retry_backoff_ms=100`, `acks="all"` (exactly-once semantics)
  - [x] `async def health_check() -> bool`: produce to `__health_check` topic and verify

- [x] **3.3 — Qdrant client (`backend/src/integrations/qdrant_client.py`)**
  - [x] `class QdrantVectorStore`: wraps `qdrant_client.AsyncQdrantClient`
  - [x] `COLLECTION_NAME = "chargeback_cases"`
  - [x] `async def ensure_collection()`: create collection if not exists with `vectors_config=VectorParams(size=1536, distance=Distance.COSINE)`, payload schema indexes on `reason_code`, `network`, `amount_bucket`, `outcome`
  - [x] `async def upsert_case(case_id: str, embedding: list[float], payload: dict)`: upsert a chargeback case with metadata payload
  - [x] `async def search_similar(query_embedding: list[float], reason_code: str | None, network: str | None, limit: int = 5) -> list[dict]`: ANN search with optional payload filters. Returns `[{"case_id": str, "score": float, "outcome": str, "narrative_summary": str}]`
  - [x] `async def health_check() -> bool`: list collections

- [x] **3.4 — LLM client (`backend/src/integrations/llm_client.py`)**
  - [x] `class GeminiLLMClient`: wraps `google.generativeai` (Gemini 2.5 Flash)
  - [x] `async def generate_structured(prompt: str, response_schema: type[BaseModel], temperature: float = 0.2) -> BaseModel`: call Gemini with JSON mode, parse response into the given Pydantic model. On parse failure: retry once with a correction prompt. On second failure: raise `LLMResponseError`
  - [x] `async def generate_text(prompt: str, temperature: float = 0.3, max_tokens: int = 4096) -> str`: plain text generation
  - [x] Implement retry decorator: exponential backoff on HTTP 429/503, max 3 retries, jitter ±500ms
  - [x] Implement token tracking: log `input_tokens`, `output_tokens`, `latency_ms` per call
  - [x] `async def health_check() -> bool`: send trivial prompt, verify response

- [x] **3.5 — Langfuse client (`backend/src/integrations/langfuse_client.py`)**
  - [x] `class LangfuseTracer`: wraps `langfuse.Langfuse`
  - [x] `def create_trace(case_id: str, name: str) -> Trace`: create a new trace for a chargeback case
  - [x] `def create_span(trace: Trace, name: str, input: dict, output: dict | None = None) -> Span`: create a span within a trace (for each agent step)
  - [x] `def create_generation(trace: Trace, name: str, prompt: str, completion: str, model: str, tokens: dict)`: log LLM generation
  - [x] `def score_trace(trace: Trace, name: str, value: float, comment: str | None = None)`: score a trace (e.g., win probability, evidence completeness)

- [x] **3.6 — MinIO/S3 client (`backend/src/integrations/minio_client.py`)**
  - [x] `class ObjectStoreClient`: wraps `boto3` S3 client configured for MinIO
  - [x] `async def upload_file(bucket: str, key: str, data: bytes, content_type: str) -> str`: returns full URL
  - [x] `async def download_file(bucket: str, key: str) -> bytes`
  - [x] `async def upload_model_artifact(model_name: str, version: str, model_bytes: bytes, metadata: dict) -> str`: uploads to `models/{model_name}/{version}/model.onnx` + `metadata.json`
  - [x] `async def download_holdout_set(version: str) -> bytes`: downloads from `holdout/{version}/data.parquet`
  - [x] `async def ensure_buckets()`: create `models`, `holdout`, `evidence`, `reports` buckets if they don't exist

- [x] **3.7 — Dependency injection (`backend/src/api/deps.py`)**
  - [x] `async def get_redis() -> RedisClient`: singleton pattern via `app.state`
  - [x] `async def get_kafka_producer() -> TypedKafkaProducer`: singleton via `app.state`
  - [x] `async def get_qdrant() -> QdrantVectorStore`: singleton via `app.state`
  - [x] `async def get_llm() -> GeminiLLMClient`: singleton via `app.state`
  - [x] `async def get_langfuse() -> LangfuseTracer`: singleton via `app.state`
  - [x] `async def get_object_store() -> ObjectStoreClient`: singleton via `app.state`
  - [x] `async def get_current_user(token: str = Depends(oauth2_scheme)) -> User`: JWT decode + DB lookup
  - [x] `async def get_current_tenant(user: User = Depends(get_current_user)) -> Tenant`: extract tenant from user
  - [x] Wire up `lifespan` handler in `main.py`: initialize all clients on startup, close connections on shutdown

### Acceptance Criteria

- [x] All clients connect to their respective Docker containers
- [x] All `health_check()` methods return `True` when services are up, `False` when down
- [x] `TypedKafkaProducer.send_event` rejects events that don't match `TOPIC_MAP`
- [x] `GeminiLLMClient.generate_structured` returns a valid Pydantic model
- [x] `RedisClient.check_rate_limit` correctly enforces limits
- [x] `QdrantVectorStore.search_similar` returns results with correct payload filtering

### Verification Gate

```bash
make up  # ensure all containers running
cd backend && pytest tests/integration/test_redis_client.py -v
cd backend && pytest tests/integration/test_kafka_producer.py -v
cd backend && pytest tests/integration/test_qdrant_client.py -v
# For LLM tests, use a mock or set GEMINI_API_KEY in .env
cd backend && pytest tests/unit/test_llm_client.py -v  # with mocked HTTP
cd backend && pytest tests/integration/test_minio_client.py -v
# Verify all health checks
curl -s http://localhost:8000/readiness | python -c "import sys,json; d=json.load(sys.stdin); print(d); assert all(v=='ok' for v in d.values())"
```

**Sign-off:** All integration clients connect, health checks pass, typed producer rejects schema mismatches.

---

## Module 4: ML Model Training, Serving & Explainability

**Goal:** Implement the full ML pipeline — feature engineering, LightGBM training, ONNX export, ONNX Runtime serving, SHAP explainability, and synthetic data generation for development.

### Key Files Created / Modified

- `backend/src/ml/__init__.py`
- `backend/src/ml/models/return_risk/features.py`
- `backend/src/ml/models/return_risk/config.py`
- `backend/src/ml/models/return_risk/train.py`
- `backend/src/ml/models/chargeback_win/features.py`
- `backend/src/ml/models/chargeback_win/train.py`
- `backend/src/ml/models/fraud_spike/isolation_forest.py`
- `backend/src/ml/models/fraud_spike/lstm_autoencoder.py`
- `backend/src/ml/models/fraud_spike/ensemble.py`
- `backend/src/ml/serving/onnx_runtime.py`
- `backend/src/ml/serving/model_registry.py`
- `backend/src/ml/explainability/shap_explainer.py`
- `backend/src/ml/explainability/formatter.py`
- `backend/scripts/generate_synthetic_data.py`
- `backend/tests/unit/test_feature_engineering.py`
- `backend/tests/unit/test_return_scoring.py`

### Implementation Checklist

- [x] **4.1 — Synthetic data generator (`backend/scripts/generate_synthetic_data.py`)**
  - [x] Generate 100,000 synthetic transactions with realistic distributions: amounts (lognormal, mean ₹2,500), timestamps (non-uniform, more activity 10am-10pm IST), categories (weighted: electronics 20%, fashion 30%, groceries 25%, other 25%)
  - [x] Generate 5,000 return requests (5% abuse rate) with labels: `is_abusive: bool`. Abuse patterns: high frequency (>3 returns/month), high value concentration, new accounts (<30 days), mismatched device fingerprints
  - [x] Generate 500 chargeback cases with outcomes (40% won, 50% lost, 10% pending) across reason codes
  - [x] Output as Parquet files to `data/synthetic/transactions.parquet`, `data/synthetic/returns.parquet`, `data/synthetic/chargebacks.parquet`
  - [x] Create time-based train/test split: 80% train (earlier dates), 20% holdout (later dates) in `data/synthetic/holdout/`

- [x] **4.2 — Return-risk feature engineering (`backend/src/ml/models/return_risk/features.py`)**
  - [x] `def compute_features(customer_id: str, order: dict, history: list[dict]) -> dict[str, float]`: computes all 50 features:
    - **Velocity features (8):** `return_count_7d`, `return_count_30d`, `return_count_90d`, `return_rate_30d` (returns/orders), `return_rate_90d`, `avg_days_to_return`, `returns_last_hour`, `returns_today`
    - **Value features (8):** `return_amount_total_30d`, `return_amount_total_90d`, `avg_return_amount`, `return_to_order_amount_ratio`, `max_single_return_amount`, `refund_rate_by_value`, `current_return_amount`, `current_order_amount`
    - **Category features (6):** `category_concentration_score` (HHI index), `high_risk_category_flag` (electronics, luxury), `category_return_rate`, `unique_categories_returned`, `same_category_streak`, `category_match_purchase_history`
    - **Account features (6):** `account_age_days`, `is_new_account` (<30 days), `total_orders`, `total_spend`, `avg_order_value`, `customer_lifetime_value`
    - **Device/behavioral features (8):** `device_fingerprint_count` (unique devices), `ip_address_count`, `shipping_address_count`, `device_age_days`, `is_new_device`, `return_reason_diversity` (unique reasons used), `time_since_delivery_hours`, `is_weekend_return`
    - **Interaction features (6):** `return_amount_to_ltv_ratio`, `velocity_acceleration_7d_vs_30d`, `amount_deviation_from_mean`, `category_x_velocity` (cross feature), `new_account_x_high_value`, `device_count_x_return_rate`
    - **Historical outcome features (8):** `previous_chargebacks`, `previous_fraud_flags`, `manual_review_count`, `denial_rate`, `override_rate`, `avg_review_time`, `escalation_count`, `last_flag_days_ago`
  - [x] `def compute_features_from_redis(redis_client, customer_id: str, order: dict) -> FeatureVector`: fetches pre-computed features from Redis, computes missing ones on-the-fly, returns `FeatureVector` with `is_degraded=True` if any feature source was unavailable

- [x] **4.3 — Return-risk model config (`backend/src/ml/models/return_risk/config.py`)**
  - [x] `FEATURE_NAMES: list[str]` — ordered list of all 50 feature names
  - [x] `CATEGORICAL_FEATURES: list[str]` — `["high_risk_category_flag", "is_new_account", "is_new_device", "is_weekend_return"]`
  - [x] `HYPERPARAMETERS: dict` — `{"objective": "binary", "metric": "binary_logloss", "num_leaves": 63, "learning_rate": 0.05, "n_estimators": 500, "scale_pos_weight": 19.0, "min_child_samples": 20, "subsample": 0.8, "colsample_bytree": 0.8, "reg_alpha": 0.1, "reg_lambda": 1.0, "max_depth": -1, "verbose": -1}`
  - [x] `CLASSIFICATION_THRESHOLD: float = 0.35` (tuned for cost-weighted optimization, not F1)

- [x] **4.4 — Return-risk model training (`backend/src/ml/models/return_risk/train.py`)**
  - [x] `def train(train_path: str, config: dict) -> lgb.Booster`: load Parquet, extract features using `features.py`, train LightGBM with `config.HYPERPARAMETERS`, return trained booster
  - [x] `def export_to_onnx(booster: lgb.Booster, output_path: str)`: convert LightGBM booster to ONNX using `onnxmltools`, save to `output_path`
  - [x] `def save_metadata(output_dir: str, feature_names: list, hyperparams: dict, train_metrics: dict)`: write `metadata.json` with model version, training timestamp, feature list, hyperparameters, training set metrics
  - [x] CLI entrypoint: `python -m src.ml.models.return_risk.train --data data/synthetic/returns.parquet --output models/return_risk/v1/`

- [x] **4.5 — Chargeback win-probability model (`backend/src/ml/models/chargeback_win/`)**
  - [x] `features.py`: `compute_features(chargeback: dict, evidence: dict) -> dict[str, float]`: 20 features including `evidence_completeness_score`, `reason_code_historical_win_rate`, `amount_bucket`, `days_to_deadline`, `has_delivery_proof`, `has_3ds_log`, `has_avs_match`, `has_customer_communication`, `similar_case_best_outcome`, `merchant_historical_win_rate`, `network_factor`, `evidence_item_count`, `narrative_length`, `transaction_age_days`
  - [x] `train.py`: same pattern as return-risk, using LightGBM with `objective="binary"`, output probability

- [x] **4.6 — Fraud-spike detector models (`backend/src/ml/models/fraud_spike/`)**
  - [x] `isolation_forest.py`: `class IsolationForestDetector` — train on normal transaction features (amount, velocity, geo spread), `detect(features: np.ndarray) -> tuple[bool, float]` returns (is_anomaly, anomaly_score). Export to ONNX
  - [x] `lstm_autoencoder.py`: `class LSTMAutoencoder(nn.Module)` — PyTorch LSTM autoencoder trained on transaction sequences (window of 60 seconds). `detect(sequence: np.ndarray) -> tuple[bool, float]` based on reconstruction error threshold. Export to ONNX via `torch.onnx.export`
  - [x] `ensemble.py`: `class FraudSpikeEnsemble` — combines Isolation Forest + LSTM autoencoder. `detect(point_features: np.ndarray, sequence_features: np.ndarray) -> AnomalyAlert`: requires both models to agree for `CRITICAL`, either one for `WARNING`, neither for `INFO`. Implements calendar-aware threshold adjustment (`threshold_multiplier: float` during registered events)

- [x] **4.7 — ONNX Runtime serving (`backend/src/ml/serving/onnx_runtime.py`)**
  - [x] `class ONNXModelServer`:
    - `__init__(model_path: str)`: load ONNX model into `onnxruntime.InferenceSession` with `providers=["CPUExecutionProvider"]`
    - `def predict(features: np.ndarray) -> np.ndarray`: run inference, return raw probabilities
    - `def predict_with_latency(features: np.ndarray) -> tuple[np.ndarray, float]`: wraps `predict` with `time.perf_counter_ns()` measurement, returns `(predictions, latency_ms)`
    - `def get_input_shape() -> tuple`: return expected input dimensions for validation
    - `def health_check() -> bool`: run a dummy prediction, verify output shape

- [x] **4.8 — Model registry (`backend/src/ml/serving/model_registry.py`)**
  - [x] `class ModelRegistry`:
    - Maintains `dict[str, ONNXModelServer]` mapping `"{model_name}:{version}"` to loaded servers
    - `def load_model(model_name: str, version: str, model_path: str)`: load into registry
    - `def get_model(model_name: str, version: str | None = None) -> ONNXModelServer`: if version is None, return champion model. Raise `ModelInferenceError` if not found
    - `def get_champion_version(model_name: str) -> str`: read from metadata or DB
    - `def set_champion(model_name: str, version: str)`: update champion pointer
    - Support A/B serving: `def predict_with_shadow(model_name: str, features: np.ndarray, shadow_version: str) -> tuple[np.ndarray, np.ndarray]`: run champion + shadow, return both predictions, log divergence

- [x] **4.9 — SHAP explainability (`backend/src/ml/explainability/shap_explainer.py`)**
  - [x] `class SHAPExplainer`:
    - `__init__(model_path: str)`: load the original LightGBM model (not ONNX) for SHAP computation
    - `def explain(features: np.ndarray, feature_names: list[str], top_k: int = 5) -> list[dict[str, float]]`: compute SHAP values using `shap.TreeExplainer`, return top-k features sorted by absolute SHAP value. Format: `[{"feature": "return_count_30d", "shap_value": 0.32, "direction": "increases_risk"}, ...]`
  - [x] `class ExplanationFormatter` (`backend/src/ml/explainability/formatter.py`):
    - `def format_for_api(shap_result: list[dict]) -> str`: convert SHAP values to human-readable text, e.g., "Risk is elevated primarily because: (1) You have made 7 returns in the last 30 days (typical is 1-2), (2) This return is for a high-value electronics item."
    - `def format_for_audit(shap_result: list[dict], full_feature_vector: dict) -> dict`: full audit-grade output with all feature values + all SHAP values

### Acceptance Criteria

- [x] Synthetic data generator produces correctly shaped Parquet files with realistic distributions
- [x] Feature engineering produces exactly 50 features with correct names and types
- [x] LightGBM model trains on synthetic data and produces a valid `.onnx` file
- [x] ONNX Runtime loads the model and produces predictions with P99 latency < 5ms
- [x] Model registry correctly manages champion/shadow models
- [x] SHAP explainer produces top-5 features with correct directionality
- [x] Fraud spike ensemble correctly applies calendar-aware thresholds

### Verification Gate

```bash
# Generate synthetic data
cd backend && python scripts/generate_synthetic_data.py
# Verify data shapes
cd backend && python -c "import pandas as pd; df=pd.read_parquet('data/synthetic/returns.parquet'); print(f'Returns: {len(df)} rows, abuse rate: {df.is_abusive.mean():.2%}')"

# Run feature engineering tests
cd backend && pytest tests/unit/test_feature_engineering.py -v

# Train model and verify ONNX export
cd backend && python -m src.ml.models.return_risk.train --data data/synthetic/returns.parquet --output models/return_risk/v1/
ls models/return_risk/v1/  # should contain model.onnx + metadata.json

# Run scoring tests (latency + correctness)
cd backend && pytest tests/unit/test_return_scoring.py -v
# Expected: P99 inference < 5ms, predictions in [0, 1], SHAP explanations non-empty

# Run fraud detection tests
cd backend && pytest tests/unit/test_fraud_detection.py -v
```

**Sign-off:** Synthetic data generated, model trained + exported to ONNX, inference P99 < 5ms, SHAP explanations verified.

---

## Module 5: Evaluation Harness & Drift Detection

**Goal:** Build the complete model evaluation pipeline that computes precision, recall, F1, AUC-ROC, and cost-weighted loss on versioned held-out test sets — the core requirement from the problem statement.

### Key Files Created / Modified

- `backend/src/ml/evaluation/harness.py`
- `backend/src/ml/evaluation/metrics.py`
- `backend/src/ml/evaluation/holdout_manager.py`
- `backend/src/ml/evaluation/drift_detector.py`
- `backend/scripts/run_evaluation.py`
- `backend/tests/evaluation/test_evaluation_harness.py`
- `backend/tests/evaluation/test_cost_weighted_metrics.py`
- `.github/workflows/model-evaluation.yml`

### Implementation Checklist

- [x] **5.1 — Metrics computation (`backend/src/ml/evaluation/metrics.py`)**
  - [x] `def compute_binary_metrics(y_true: np.ndarray, y_prob: np.ndarray, threshold: float) -> CostWeightedMetrics`:
    - Compute confusion matrix at the given threshold
    - Compute precision, recall, F1, AUC-ROC
    - Compute cost-weighted loss: `(fp_cost * fp_count + fn_cost * fn_count) / len(y_true)`
    - Return `CostWeightedMetrics` Pydantic model
  - [x] `def find_optimal_threshold(y_true: np.ndarray, y_prob: np.ndarray, fp_cost: float, fn_cost: float, thresholds: np.ndarray = np.arange(0.05, 0.95, 0.01)) -> tuple[float, CostWeightedMetrics]`: sweep thresholds, return the one minimizing cost-weighted loss
  - [x] `def compute_calibration_curve(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> dict`: returns `{"bin_means": [...], "fraction_positive": [...], "ece": float}` (Expected Calibration Error)
  - [x] `def compute_threshold_curve(y_true: np.ndarray, y_prob: np.ndarray, fp_cost: float, fn_cost: float) -> list[dict]`: returns `[{"threshold": float, "precision": float, "recall": float, "cost_weighted_loss": float}, ...]` for dashboard visualization

- [x] **5.2 — Holdout set manager (`backend/src/ml/evaluation/holdout_manager.py`)**
  - [x] `class HoldoutManager`:
    - `__init__(object_store: ObjectStoreClient)`
    - `def create_holdout(data: pd.DataFrame, version: str) -> str`: compute SHA-256 hash of data bytes, upload to `holdout/{version}/data.parquet` + `holdout/{version}/manifest.json` (with hash, row count, class distribution, creation timestamp). Return S3 URL
    - `def load_holdout(version: str) -> tuple[pd.DataFrame, dict]`: download and verify SHA-256 hash matches manifest, return (data, manifest_metadata). Raise `ValueError` on hash mismatch (data integrity check)
    - `def list_versions() -> list[dict]`: list all holdout versions with metadata
    - `def verify_no_overlap(train_data: pd.DataFrame, holdout: pd.DataFrame, key_col: str) -> bool`: assert zero overlap on key column (prevents data leakage)

- [x] **5.3 — Evaluation harness (`backend/src/ml/evaluation/harness.py`)**
  - [x] `class EvaluationHarness`:
    - `__init__(model_registry: ModelRegistry, holdout_manager: HoldoutManager, evaluation_repo: EvaluationRepository, object_store: ObjectStoreClient)`
    - `async def evaluate(model_name: str, model_version: str, holdout_version: str, fp_cost: Decimal, fn_cost: Decimal) -> EvaluationReport`:
      1. Load holdout set via `holdout_manager.load_holdout(holdout_version)`
      2. Load model via `model_registry.get_model(model_name, model_version)`
      3. Extract features using the model's feature pipeline
      4. Run inference on all holdout samples
      5. Compute metrics via `compute_binary_metrics`
      6. Find optimal threshold via `find_optimal_threshold`
      7. Compare against champion model (if exists): compute improvement delta
      8. Generate full report (metrics table, ROC curve data, calibration curve, threshold curve)
      9. Upload report to S3 as JSON
      10. Persist `EvaluationRun` to PostgreSQL
      11. Return `EvaluationReport`
    - `async def gate_check(report: EvaluationReport, min_precision: float = 0.7, min_recall: float = 0.5, max_cost_increase_pct: float = 5.0) -> tuple[bool, str]`: returns (passes_gate, reason). Fails if precision < min_precision, recall < min_recall, or cost_weighted_loss is >5% worse than champion
    - `async def promote_if_better(report: EvaluationReport) -> bool`: if `is_improvement` and passes gate, promote to champion. Return True if promoted

- [x] **5.4 — Drift detector (`backend/src/ml/evaluation/drift_detector.py`)**
  - [x] `def compute_psi(reference: np.ndarray, current: np.ndarray, n_bins: int = 10) -> float`: Population Stability Index
  - [x] `def compute_kl_divergence(reference: np.ndarray, current: np.ndarray, n_bins: int = 10) -> float`: KL-divergence with smoothing (add epsilon to avoid log(0))
  - [x] `def detect_drift(reference_data: pd.DataFrame, current_data: pd.DataFrame, feature_names: list[str]) -> list[DriftReport]`: compute PSI + KL for each feature, return list of `DriftReport` with `is_drifted` and `requires_retrain` flags
  - [x] `def compute_prediction_drift(reference_preds: np.ndarray, current_preds: np.ndarray) -> dict`: compare prediction distributions to detect model-level drift (not just feature-level)

- [x] **5.5 — Evaluation CLI (`backend/scripts/run_evaluation.py`)**
  - [x] Argparse CLI: `python scripts/run_evaluation.py --model return_risk --version v1 --holdout v1 --fp-cost 500 --fn-cost 2000`
  - [x] Prints metrics table to stdout
  - [x] Outputs full report to S3
  - [x] Exits with code 0 if gate passes, code 1 if fails (for CI integration)

- [x] **5.6 — CI model evaluation gate (`.github/workflows/model-evaluation.yml`)**
  - [x] Trigger on changes to `backend/src/ml/models/**`, `models/**`, `data/holdout/**`
  - [x] Run `scripts/run_evaluation.py` for each modified model
  - [x] Fail the pipeline if any model fails the gate check
  - [ ] Post evaluation summary as a PR comment (precision, recall, cost-weighted loss, delta vs. champion)

### Acceptance Criteria

- [ ] `compute_binary_metrics` produces correct precision/recall/F1 for a known confusion matrix
- [ ] `find_optimal_threshold` returns a threshold that minimizes cost-weighted loss (verified with hand-calculated example)
- [ ] `HoldoutManager` detects data corruption (hash mismatch)
- [ ] `HoldoutManager.verify_no_overlap` catches train/test leakage
- [ ] Full pipeline: train on synthetic data → evaluate on holdout → generate report → gate check → outputs match expected metrics
- [ ] Drift detector correctly flags features with PSI > 0.1 as drifted

### Verification Gate

```bash
cd backend && pytest tests/evaluation/test_cost_weighted_metrics.py -v
# Expected: verify cost_weighted_loss formula with known values:
#   fp_cost=500, fn_cost=2000, fp=10, fn=5, total=1000
#   expected = (500*10 + 2000*5) / 1000 = 15.0

cd backend && pytest tests/evaluation/test_evaluation_harness.py -v
# Expected: full pipeline test with synthetic data

cd backend && python scripts/run_evaluation.py --model return_risk --version v1 --holdout v1 --fp-cost 500 --fn-cost 2000
# Expected: prints metrics, exits 0 if gate passes
```

**Sign-off:** Cost-weighted metrics are mathematically verified, holdout integrity checks work, evaluation pipeline produces correct reports, CI gate passes.

---

## Module 6: Streaming Pipeline & Feature Store

**Goal:** Build the Faust-based Kafka stream processing layer that computes real-time features, detects fraud spikes, and feeds the entity graph — connecting raw transaction events to the ML scoring engine.

### Key Files Created / Modified

- `backend/src/streaming/__init__.py`
- `backend/src/streaming/app.py`
- `backend/src/streaming/processors/transaction_processor.py`
- `backend/src/streaming/processors/anomaly_processor.py`
- `backend/src/streaming/processors/graph_updater.py`
- `backend/src/streaming/tables/velocity_counters.py`
- `backend/src/streaming/tables/amount_windows.py`
- `backend/tests/integration/test_kafka_pipeline.py`

### Implementation Checklist

- [x] **6.1 — Faust application (`backend/src/streaming/app.py`)**
  - [x] Create Faust app: `app = faust.App("risk-manager", broker=settings.KAFKA_BOOTSTRAP_SERVERS, store="rocksdb://", topic_partitions=8)`
  - [x] Register agents (stream processors): `transaction_agent`, `anomaly_agent`, `graph_agent`
  - [x] Register tables: `velocity_table`, `amount_window_table`
  - [x] Add health check endpoint: `@app.page("/health")` returning `{"status": "ok"}`

- [x] **6.2 — Transaction processor (`backend/src/streaming/processors/transaction_processor.py`)**
  - [x] Define Faust model `TransactionRecord(faust.Record)` mirroring `TransactionEvent` fields
  - [x] Define topic: `transactions_topic = app.topic("transactions.raw", value_type=TransactionRecord)`
  - [x] Agent `@app.agent(transactions_topic)`:
    - For each transaction:
      1. Update velocity counters: increment `velocity:{tenant_id}:{customer_id}:1m`, `:5m`, `:1h`, `:24h` in the Faust table (windowed)
      2. Update amount windows: append amount to `amounts:{tenant_id}:{customer_id}:1h` sliding window, compute running mean/stddev
      3. Write computed features to Redis: `SET features:{tenant_id}:{customer_id} {json} EX 3600`
      4. Forward to anomaly processor if velocity exceeds baseline by >3x

- [x] **6.3 — Velocity counters table (`backend/src/streaming/tables/velocity_counters.py`)**
  - [x] `velocity_table = app.Table("velocity_counters", default=int, partitions=8)` with tumbling windows: 1 minute, 5 minutes, 1 hour
  - [x] Key format: `{tenant_id}:{customer_id}`
  - [x] Expose `get_velocity(tenant_id, customer_id) -> dict[str, int]` returning `{"1m": count, "5m": count, "1h": count}`

- [x] **6.4 — Amount windows table (`backend/src/streaming/tables/amount_windows.py`)**
  - [x] `amount_table = app.Table("amount_windows", default=list, partitions=8)` storing sliding window of amounts
  - [x] `get_amount_stats(tenant_id, customer_id) -> dict[str, float]`: returns `{"mean": float, "stddev": float, "p95": float, "count": int}` from the window

- [x] **6.5 — Anomaly processor (`backend/src/streaming/processors/anomaly_processor.py`)**
  - [x] Subscribe to `transactions.raw` with a separate agent for anomaly detection
  - [x] Maintain per-`(tenant_id, mcc, city)` segment baselines using exponential moving average (EMA) with `alpha=0.1`
  - [x] Compute deviation factor: `current_tps / baseline_tps`
  - [x] If deviation > 3x: publish `AnomalyAlert` to `alerts.outbound` topic with `severity=WARNING`
  - [x] If deviation > 10x: `severity=CRITICAL`
  - [x] Calendar adjustment: load registered events from PostgreSQL (cached in Faust table), multiply threshold by `2.0` during known events (e.g., Diwali sale)
  - [x] Run `FraudSpikeEnsemble.detect()` on flagged segments to classify as `organic_spike`, `attack`, or `uncertain`

- [x] **6.6 — Graph updater (`backend/src/streaming/processors/graph_updater.py`)**
  - [x] Subscribe to `transactions.raw`
  - [x] For each transaction, emit Neo4j Cypher mutations (batched, every 100 events or 5 seconds):
    - `MERGE (b:Buyer {id: $customer_id, tenant_id: $tenant_id})`
    - `MERGE (s:Seller {id: $merchant_id})`
    - `MERGE (a:Address {hash: $address_hash})`
    - `MERGE (d:Device {fingerprint: $device_fingerprint})`
    - `MERGE (p:PaymentInstrument {token: $payment_token})`
    - `CREATE (b)-[:BOUGHT_FROM {amount: $amount, timestamp: $ts}]->(s)`
    - `MERGE (b)-[:USES]->(d)`, `(b)-[:SHIPS_TO]->(a)`, `(b)-[:PAYS_WITH]->(p)`
  - [x] Use Neo4j async driver with batch writes for throughput

### Acceptance Criteria

- [x] Faust worker starts and connects to Kafka without errors
- [x] Publishing a `TransactionEvent` to `transactions.raw` results in updated Redis features within 500ms
- [x] Velocity counters increment correctly across time windows
- [x] Anomaly processor detects a 5x spike and publishes an alert to `alerts.outbound`
- [x] Calendar adjustment prevents false alerts during registered events
- [x] Graph updater creates correct Neo4j nodes and relationships

### Verification Gate

```bash
make up  # all services including Kafka, Redis, Neo4j
cd backend && faust -A src.streaming.app worker -l info &  # start Faust worker

# Publish test transactions
cd backend && pytest tests/integration/test_kafka_pipeline.py -v
# Expected tests:
#   - test_transaction_updates_redis_features: publish 10 transactions, verify Redis features
#   - test_velocity_counters: publish burst, verify counters
#   - test_anomaly_detection: publish 100 transactions in 1 second, verify alert
#   - test_calendar_adjustment: register event, publish spike, verify no alert
#   - test_graph_updater: publish transactions, verify Neo4j nodes/edges

kill %1  # stop Faust worker
```

**Sign-off:** Stream processing pipeline operates end-to-end, features land in Redis within latency budget, anomaly detection fires correctly.

---

## Module 7: AI Agent Pipeline (Chargeback Evidence Responder)

**Goal:** Build the LangGraph-based multi-agent pipeline for automated chargeback evidence assembly, narrative generation, and confidence scoring — the primary AI module.

### Key Files Created / Modified

- `backend/src/agents/__init__.py`
- `backend/src/agents/state.py`
- `backend/src/agents/orchestrator.py`
- `backend/src/agents/evidence_assembler.py`
- `backend/src/agents/narrative_generator.py`
- `backend/src/agents/confidence_scorer.py`
- `backend/src/agents/tools/order_lookup.py`
- `backend/src/agents/tools/shipping_tracker.py`
- `backend/src/agents/tools/payment_log_fetcher.py`
- `backend/src/agents/tools/similar_case_search.py`
- `backend/src/agents/tools/template_renderer.py`
- `backend/src/agents/prompts/evidence_summary.py`
- `backend/src/agents/prompts/representment_narrative.py`
- `backend/src/agents/prompts/confidence_assessment.py`
- `backend/tests/integration/test_agent_pipeline.py`

### Implementation Checklist

- [x] **7.1 — Agent state definition (`backend/src/agents/state.py`)**
  - [x] Define `class ChargebackAgentState(TypedDict)`: `case_id: str`, `tenant_id: str`, `chargeback: dict` (serialized `ChargebackNotification`), `reason_code: str`, `network: str`, `evidence_checklist: list[str]`, `evidence_items: list[dict]`, `evidence_bundle: dict | None`, `narrative_draft: str | None`, `win_probability: float | None`, `recommendation: str | None`, `errors: list[str]`, `current_step: str`, `trace_id: str`

- [x] **7.2 — Agent tools**
  - [x] `order_lookup.py`: `@tool def lookup_order(order_id: str, tenant_id: str) -> dict`: fetch from PostgreSQL — returns order details (items, amounts, dates, customer info, shipping address). Returns `{"found": False}` if not found. Wrapped with `EvidenceRetrievalError` handling
  - [x] `shipping_tracker.py`: `@tool def track_shipment(tracking_number: str, carrier: str) -> dict`: mock external shipping API call — returns `{"delivered": bool, "delivery_date": str, "signed_by": str, "proof_url": str}`. In production, integrate with Delhivery/Shiprocket/Bluedart APIs
  - [x] `payment_log_fetcher.py`: `@tool def fetch_payment_logs(transaction_id: str, tenant_id: str) -> dict`: fetch 3DS authentication logs, AVS match results, IP geolocation from payment gateway. Returns `{"3ds_authenticated": bool, "avs_match": str, "ip_country": str, "ip_city": str}`
  - [x] `similar_case_search.py`: `@tool def search_similar_cases(case_summary: str, reason_code: str, network: str, limit: int = 5) -> list[dict]`: embed `case_summary` using embedding model, search Qdrant with payload filters on `reason_code` + `network`. Returns top-k similar past cases with outcomes and winning narratives
  - [x] `template_renderer.py`: `@tool def render_template(network: str, reason_code: str, evidence: dict) -> str`: select the correct card network template (Visa/MC/RuPay), render with evidence fields. Templates stored as Jinja2 templates in `backend/src/agents/prompts/templates/`

- [x] **7.3 — Evidence assembler agent (`backend/src/agents/evidence_assembler.py`)**
  - [x] `def evidence_assembler_node(state: ChargebackAgentState) -> ChargebackAgentState`:
    1. Extract `evidence_checklist` from state (set by reason code mapper)
    2. For each required evidence type, call the appropriate tool in parallel (using LangGraph's `Send` API):
       - `delivery_proof` → `track_shipment`
       - `avs_match` → `fetch_payment_logs`
       - `3ds_log` → `fetch_payment_logs`
       - `order_confirmation` → `lookup_order`
       - `customer_communication` → `lookup_order` (communications sub-field)
    3. Collect results, compute `completeness_score = found_items / required_items`
    4. Build `EvidenceBundle` and update state
    5. If `completeness_score < 0.5`: set `recommendation = "accept_loss"` and skip narrative generation
    6. Log all tool calls to Langfuse via `LangfuseTracer`

- [x] **7.4 — Narrative generator agent (`backend/src/agents/narrative_generator.py`)**
  - [x] `async def narrative_generator_node(state: ChargebackAgentState) -> ChargebackAgentState`:
    1. Retrieve similar winning cases from Qdrant (via `similar_case_search`)
    2. Build prompt using `representment_narrative.py` template:
       - Include reason code description, evidence summary, similar case narratives
       - Specify output format: structured sections (Transaction Summary, Evidence Presented, Merchant Response, Requested Action)
       - Specify card network formatting requirements
    3. Call `GeminiLLMClient.generate_text` with assembled prompt
    4. Validate output format (must contain all required sections)
    5. On validation failure: retry with correction prompt (max 2 retries)
    6. On persistent failure: fall back to `template_renderer` tool for basic template-based narrative
    7. Update state with `narrative_draft`
    8. Log generation to Langfuse with prompt version, token usage, latency

- [x] **7.5 — Confidence scorer agent (`backend/src/agents/confidence_scorer.py`)**
  - [x] `async def confidence_scorer_node(state: ChargebackAgentState) -> ChargebackAgentState`:
    1. Extract features from evidence bundle and narrative using `chargeback_win/features.py`
    2. Run ONNX inference via `model_registry.get_model("chargeback_win")`
    3. Compute SHAP explanation
    4. Set `win_probability` and `recommendation`:
       - `win_probability > 0.6` → `"respond"`
       - `win_probability <= 0.6` → `"accept_loss"` (but still allow human override)
    5. Update state

- [x] **7.6 — Prompt templates**
  - [x] `evidence_summary.py`: template for summarizing collected evidence into a structured format for the LLM
  - [x] `representment_narrative.py`: main narrative generation prompt with few-shot examples from similar cases, network-specific formatting rules. Include explicit instruction: "Do not fabricate evidence. Only reference evidence items provided in the context."
  - [x] `confidence_assessment.py`: prompt for the LLM to provide a qualitative assessment alongside the ML score

- [x] **7.7 — LangGraph orchestrator (`backend/src/agents/orchestrator.py`)**
  - [x] Build `StateGraph(ChargebackAgentState)` with nodes:
    1. `parse_notification` → extract and validate chargeback data, map reason code to evidence checklist
    2. `assemble_evidence` → `evidence_assembler_node`
    3. `generate_narrative` → `narrative_generator_node` (conditional: skip if `recommendation == "accept_loss"`)
    4. `score_confidence` → `confidence_scorer_node` (conditional: skip if no narrative)
    5. `human_review` → checkpoint node (LangGraph `interrupt_before` for human-in-the-loop)
    6. `finalize` → persist final case state to DB
  - [x] Add edges: `parse → assemble → generate (conditional) → score (conditional) → human_review → finalize`
  - [x] Add error handling edge: any node failure → `handle_error` node that logs the error, sets `status = "ERROR"`, and creates an alert
  - [x] Compile graph: `graph = workflow.compile(checkpointer=MemorySaver())` for state persistence across restarts
  - [x] Implement `async def process_chargeback(notification: ChargebackNotification, tenant_id: UUID) -> RepresentmentDraft`: entry point that creates initial state and invokes the graph

- [x] **7.8 — Input sanitization for defense-only constraint**
  - [x] Implement `sanitize_input(text: str) -> str` in `backend/src/agents/tools/__init__.py`:
    - Strip control characters
    - Detect and escape common prompt injection patterns (e.g., "ignore previous instructions", "system:", "assistant:")
    - Truncate inputs exceeding 10,000 characters
    - Log any sanitization actions to audit trail
  - [x] Apply `sanitize_input` to all text fields before passing to LLM (dispute description, customer communications)

### Acceptance Criteria

- [ ] Orchestrator processes a complete chargeback from notification → evidence → narrative → confidence score → draft
- [ ] Evidence assembler correctly calls tools in parallel and computes completeness score
- [ ] Narrative generator produces network-specific formatted output
- [ ] Narrative generator falls back to template on LLM failure
- [ ] Confidence scorer produces a probability in [0, 1] with SHAP explanation
- [ ] Human-in-the-loop checkpoint pauses execution until analyst action
- [ ] All agent steps are traced in Langfuse with prompt versions and token usage
- [ ] Input sanitization strips injection patterns without corrupting legitimate text

### Verification Gate

```bash
cd backend && pytest tests/integration/test_agent_pipeline.py -v
# Expected tests (using mocked LLM and mock merchant data):
#   - test_full_pipeline_happy_path: notification → draft with win_probability
#   - test_incomplete_evidence_accepts_loss: missing >50% evidence → accept_loss
#   - test_llm_fallback_to_template: mock LLM failure → template-based narrative
#   - test_prompt_injection_sanitized: injection attempt → sanitized before LLM
#   - test_duplicate_notification_rejected: same ARN → DuplicateIngestionError
#   - test_deadline_computation: Visa → 30d, MC → 45d
#   - test_langfuse_tracing: verify trace spans created
```

**Sign-off:** Agent pipeline processes chargebacks end-to-end, falls back gracefully on failures, sanitizes inputs, and produces auditable traces.

---

## Module 8: Service Layer & Business Logic

**Goal:** Implement the service layer that wires together ML models, agents, feature store, and policy engine into coherent business workflows for each risk module.

### Key Files Created / Modified

- `backend/src/services/__init__.py`
- `backend/src/services/chargeback_service.py`
- `backend/src/services/return_scoring_service.py`
- `backend/src/services/fraud_detection_service.py`
- `backend/src/services/case_management_service.py`
- `backend/src/services/notification_service.py`

### Implementation Checklist

- [x] **8.1 — Return scoring service (`backend/src/services/return_scoring_service.py`)**
  - [x] `class ReturnScoringService`:
    - Dependencies: `ModelRegistry`, `RedisClient`, `CaseRepository`, `SHAPExplainer`, `ExplanationFormatter`
    - `async def score(request: ReturnScoreRequest, tenant: Tenant) -> ReturnScoreResponse`:
      1. Fetch features from Redis (`get_feature_vector`). If unavailable: compute on-the-fly from DB (degraded mode, set `is_degraded=True`)
      2. Run ONNX inference via `model_registry.get_model("return_risk")`
      3. Convert probability to risk score (0-100): `int(probability * 100)`
      4. Map to `RiskTier` using `tenant.policy_config` thresholds
      5. Apply policy: map tier to decision (`auto_approve`, `manual_review`, `auto_deny`)
      6. Apply high-value customer override: if `policy_config.high_value_customer_override` and customer LTV > threshold, downgrade `auto_deny` to `manual_review`
      7. Compute SHAP explanation (top-5 features)
      8. Format explanation for API response
      9. Persist decision record to PostgreSQL (async, non-blocking)
      10. Emit `ReturnEvent` to Kafka (async, non-blocking)
      11. Record Prometheus metrics (inference_latency, score_distribution, tier_distribution)
      12. Return `ReturnScoreResponse` with all fields populated
    - Total latency budget: ≤ 50ms P50, ≤ 150ms P99. If feature fetch exceeds 100ms: timeout and use degraded features

- [x] **8.2 — Chargeback service (`backend/src/services/chargeback_service.py`)**
  - [x] `class ChargebackService`:
    - Dependencies: `ChargebackRepository`, `CaseRepository`, `TypedKafkaProducer`, agent `process_chargeback`
    - `async def ingest(request: ChargebackIngestRequest, tenant: Tenant) -> ChargebackIngestResponse`:
      1. Parse raw payload into `ChargebackNotification` (with idempotency check)
      2. Create `Case` record (source=CHARGEBACK)
      3. Create `ChargebackRecord`
      4. Emit `ChargebackEvent(event_type="chargeback.received")` to Kafka
      5. Enqueue agent processing via Celery task (priority based on deadline urgency)
      6. Return `ChargebackIngestResponse` with case_id and deadline
    - `async def process(case_id: UUID, tenant_id: UUID)`: Celery task that runs the LangGraph agent pipeline, updates case status throughout
    - `async def review(case_id: UUID, action: Literal["approve", "edit", "reject"], edits: dict | None, actor_id: UUID)`:
      - `approve`: set status → SUBMITTED, record in audit log
      - `edit`: update narrative/evidence, regenerate confidence score, set status → DRAFT_READY
      - `reject`: set status → ACCEPTED_LOSS, record reason in audit log
    - `async def get_pending_reviews(tenant_id: UUID) -> list[Case]`: return cases with status DRAFT_READY ordered by deadline proximity
    - `async def get_deadline_alerts(tenant_id: UUID) -> list[Case]`: return cases approaching deadline (within 48h)

- [x] **8.3 — Fraud detection service (`backend/src/services/fraud_detection_service.py`)**
  - [x] `class FraudDetectionService`:
    - Dependencies: `TypedKafkaProducer`, `CaseRepository`, `NotificationService`
    - `async def handle_alert(alert: AnomalyAlert, tenant: Tenant)`:
      1. Create `Case` record (source=FRAUD_ALERT) if severity >= WARNING
      2. Route alert via `NotificationService` based on severity → channel mapping
      3. Persist alert details to PostgreSQL
    - `async def register_event(tenant_id: UUID, event_name: str, start: datetime, end: datetime)`: register a known sale/festival event to adjust anomaly thresholds
    - `async def get_active_alerts(tenant_id: UUID) -> list[AnomalyAlert]`

- [x] **8.4 — Case management service (`backend/src/services/case_management_service.py`)**
  - [x] `class CaseManagementService`:
    - Dependencies: `CaseRepository`, audit trail integration
    - `async def assign(case_id: UUID, tenant_id: UUID, user_id: UUID, actor_id: UUID)`: assign case to analyst with audit log
    - `async def update_status(case_id: UUID, tenant_id: UUID, new_status: CaseStatus, actor_id: UUID, resolution: str | None = None)`: transition status with validation (e.g., can't go from LOST back to DRAFT_READY), write audit log
    - `async def get_dashboard_stats(tenant_id: UUID) -> dict`: aggregate case counts by status, source, priority. Include `avg_resolution_time`, `approaching_deadline_count`, `win_rate_last_90d`
    - `async def search(tenant_id: UUID, query: str, filters: dict, page: int, size: int) -> tuple[list[Case], int]`: full-text search + filter on cases

- [x] **8.5 — Notification service (`backend/src/services/notification_service.py`)**
  - [x] `class NotificationService`:
    - `async def send(channel: NotificationChannel, recipient: str, subject: str, body: str, metadata: dict)`: dispatch notification. For MVP: implement `EMAIL` (via SMTP/SendGrid) and `SLACK` (via webhook). `PAGERDUTY` and `SMS` as stubs raising `NotImplementedError`
    - `async def route_alert(alert: AnomalyAlert, tenant: Tenant)`: look up tenant notification config, send to appropriate channels based on severity mapping
    - `async def send_deadline_warning(case: Case, hours_remaining: int)`: templated deadline warning message

### Acceptance Criteria

- [x] `ReturnScoringService.score` returns response within 150ms P99 (with Redis warm)
- [x] `ReturnScoringService.score` falls back to degraded mode when Redis is down
- [ ] `ChargebackService.ingest` is idempotent (duplicate ARN → error, not duplicate case)
- [ ] `ChargebackService.review` writes audit log entries for every action
- [ ] Case status transitions are validated (invalid transitions rejected)
- [ ] Dashboard stats aggregate correctly across all case sources

### Verification Gate

```bash
cd backend && pytest tests/unit/test_return_scoring.py -v
cd backend && pytest tests/unit/test_chargeback_service.py -v
cd backend && pytest tests/unit/test_case_management.py -v
# Expected: all service-layer tests pass with mocked dependencies
# Specific assertions:
#   - Return scoring latency < 150ms with mock Redis
#   - Chargeback idempotency verified
#   - Case status transition validation verified
#   - Audit logs created for all mutations
```

**Sign-off:** All service layer tests pass, latency budgets met, idempotency and audit trails verified.

---

## Module 9: REST API Layer & Middleware

**Goal:** Expose all service-layer functionality through versioned REST API endpoints with authentication, rate limiting, request tracing, and OpenAPI documentation.

### Key Files Created / Modified

- `backend/src/api/middleware/auth.py`
- `backend/src/api/middleware/rate_limit.py`
- `backend/src/api/middleware/request_id.py`
- `backend/src/api/v1/__init__.py`
- `backend/src/api/v1/chargebacks.py`
- `backend/src/api/v1/returns.py`
- `backend/src/api/v1/fraud.py`
- `backend/src/api/v1/cases.py`- [x] **9.1 — Authentication middleware (`backend/src/api/middleware/auth.py`)**
  - [x] JWT-based authentication using `python-jose`:
    - `def create_access_token(user_id: UUID, tenant_id: UUID, role: str, expires_delta: timedelta = timedelta(hours=8)) -> str`
    - `async def verify_token(token: str) -> dict`: decode JWT, return payload with `user_id`, `tenant_id`, `role`
  - [x] RBAC decorator: `def require_role(*roles: str)` → FastAPI `Depends` that checks `current_user.role in roles`
  - [x] API key authentication (for machine-to-machine): `async def verify_api_key(x_api_key: str = Header())` → look up tenant by hashed API key
  - [x] Support both: JWT (for dashboard users) and API key (for webhook/integration callers)

- [x] **9.2 — Rate limiting middleware (`backend/src/api/middleware/rate_limit.py`)**
  - [x] Redis-backed sliding window rate limiter:
    - `async def rate_limit(identifier: str, limit: int, window_seconds: int)`: uses `RedisClient.check_rate_limit`
    - Return `429 Too Many Requests` with `Retry-After` header when exceeded
  - [x] Per-endpoint configuration (from PRD §3.5):
    - `/v1/returns/score`: 100 req/s per tenant
    - `/v1/chargebacks/ingest`: 500 req/s per source
    - `/v1/*` (dashboard): 120 req/min per user

- [x] **9.3 — Request ID middleware (`backend/src/api/middleware/request_id.py`)**
  - [x] Generate `X-Request-ID` (UUID4) if not present in request headers
  - [x] Propagate to all downstream calls (DB queries, Kafka events, LLM calls)
  - [x] Include in all response headers
  - [x] Set as OpenTelemetry trace context

- [x] **9.4 — Chargeback endpoints (`backend/src/api/v1/chargebacks.py`)**
  - [x] `POST /v1/chargebacks/ingest`: accept `ChargebackIngestRequest`, auth via API key, rate limit 500/s. Returns `ChargebackIngestResponse` with `202 Accepted`
  - [x] `GET /v1/chargebacks/{case_id}`: retrieve full chargeback case with evidence, narrative, and score. Auth: JWT, roles `analyst`, `admin`
  - [x] `GET /v1/chargebacks/pending`: list cases with status `DRAFT_READY` for review queue. Supports pagination (`?page=1&size=20`) and sorting (`?sort=deadline_asc`)
  - [x] `POST /v1/chargebacks/{case_id}/review`: submit review action (`approve`, `edit`, `reject`). Auth: JWT, roles `analyst`, `admin`. Body: `{"action": "approve" | "edit" | "reject", "edits": {...}}`. Creates audit log entry
  - [x] `GET /v1/chargebacks/deadlines`: list approaching deadlines (within 48h). Auth: JWT
  - [x] `POST /v1/chargebacks/upload`: file upload endpoint for batch chargeback ingestion (CSV/ISO 8583). Auth: API key. Returns `{"accepted": int, "rejected": int, "errors": [...]}`

- [x] **9.5 — Return scoring endpoints (`backend/src/api/v1/returns.py`)**
  - [x] `POST /v1/returns/score`: accept `ReturnScoreRequest`, auth via API key, rate limit 100/s/tenant. Returns `ReturnScoreResponse`. Must respond within 300ms hard ceiling (return `503` if timeout)
  - [x] `GET /v1/returns/history`: paginated history of return scoring decisions for a tenant. Supports filters: `?customer_id=`, `?risk_tier=`, `?date_from=`, `?date_to=`
  - [x] `PUT /v1/returns/policy`: update `PolicyConfig` for a tenant. Auth: JWT, role `admin`. Validates thresholds are in order (low < medium < high)

- [x] **9.6 — Fraud alert endpoints (`backend/src/api/v1/fraud.py`)**
  - [x] `GET /v1/fraud/alerts`: list active alerts for a tenant. Supports filters: `?severity=`, `?classification=`, `?from=`, `?to=`
  - [x] `GET /v1/fraud/alerts/{alert_id}`: detailed alert view with transaction IDs, geographic spread, velocity profile
  - [x] `POST /v1/fraud/events`: register a known sale/festival event. Body: `{"name": str, "start": datetime, "end": datetime, "threshold_multiplier": float}`
  - [x] `POST /v1/fraud/alerts/{alert_id}/acknowledge`: mark alert as acknowledged. Auth: JWT, roles `analyst`, `admin`

- [x] **9.7 — Case management endpoints (`backend/src/api/v1/cases.py`)**
  - [x] `GET /v1/cases`: list all cases with filters (`?source=`, `?status=`, `?assigned_to=`, `?priority=`) and pagination
  - [x] `GET /v1/cases/{case_id}`: full case detail with audit trail
  - [x] `PATCH /v1/cases/{case_id}`: update case (assign, change status). Auth: JWT
  - [x] `GET /v1/cases/{case_id}/audit`: audit trail for a specific case
  - [x] `GET /v1/cases/stats`: dashboard statistics (case counts by status/source, win rate, avg resolution time)

- [x] **9.8 — Metrics & evaluation endpoints (`backend/src/api/v1/metrics.py`)**
  - [x] `GET /v1/metrics/evaluation/{model_name}`: list evaluation runs for a model with metrics
  - [x] `GET /v1/metrics/evaluation/{model_name}/latest`: latest evaluation report
  - [x] `GET /v1/metrics/drift/{model_name}`: latest drift report per feature
  - [x] `GET /v1/metrics/cost-summary`: ₹-denominated cost summary: `{"total_fp_cost": Decimal, "total_fn_cost": Decimal, "total_savings": Decimal, "period": str}`
  - [x] `GET /v1/metrics/prometheus`: Prometheus-compatible metrics endpoint (histogram: inference_latency, counter: requests_total, gauge: active_cases)

- [ ] **9.9 — Router assembly (`backend/src/main.py` update)**
  - [ ] Include all routers under `/api/v1/` prefix
  - [ ] Add middleware stack in order: request_id → rate_limit → auth → CORS
  - [ ] Add OpenTelemetry FastAPI instrumentation
  - [ ] Add exception handlers: `SchemaValidationError → 422`, `CaseNotFoundError → 404`, `DuplicateIngestionError → 409`, `ModelInferenceError → 503`, `DeadlineExceededError → 410`, `RiskManagerError → 500`

### Acceptance Criteria

- [ ] All endpoints return correct HTTP status codes
- [ ] Authentication rejects invalid/expired tokens with 401
- [ ] RBAC prevents analysts from accessing admin-only endpoints
- [ ] Rate limiter returns 429 with correct `Retry-After` header
- [ ] Request IDs propagate through the full request lifecycle
- [ ] `/v1/returns/score` responds within 300ms under load
- [ ] OpenAPI docs auto-generated at `/docs` with correct schemas

### Verification Gate

```bash
cd backend && pytest tests/integration/test_api_chargebacks.py -v
cd backend && pytest tests/integration/test_api_returns.py -v
# Expected tests:
#   - test_ingest_chargeback_returns_202
#   - test_ingest_duplicate_returns_409
#   - test_score_return_valid_request
#   - test_score_return_timeout_returns_503
#   - test_auth_rejects_invalid_token
#   - test_rbac_blocks_unauthorized_role
#   - test_rate_limit_returns_429
#   - test_request_id_propagation

# Load test (optional, stretch)
# pip install locust
# locust -f tests/load/locustfile.py --host=http://localhost:8000 --users=100 --run-time=30s
```

**Sign-off:** All API endpoints return correct responses, auth/RBAC/rate-limiting enforced, request tracing works end-to-end.

---

## Module 10: Graph Analysis (Abuse-Ring Sentinel)

**Goal:** Implement the Neo4j-backed graph analysis pipeline for detecting coordinated abuse rings through community detection algorithms.

### Key Files Created / Modified

- `backend/src/graph/__init__.py`
- `backend/src/graph/neo4j_client.py`
- `backend/src/graph/community_detection.py`
- `backend/src/graph/ring_scorer.py`

### Implementation Checklist

- [ ] **10.1 — Neo4j client (`backend/src/graph/neo4j_client.py`)**
  - [ ] `class Neo4jClient`: wraps `neo4j.AsyncDriver`
  - [ ] `async def ensure_constraints()`: create uniqueness constraints on `Buyer.id`, `Seller.id`, `Device.fingerprint`, `Address.hash`, `PaymentInstrument.token`
  - [ ] `async def ensure_indexes()`: create indexes on `(tenant_id)` for all node types
  - [ ] `async def batch_merge_nodes(nodes: list[dict])`: batch UNWIND + MERGE for high-throughput graph building
  - [ ] `async def batch_merge_edges(edges: list[dict])`: batch edge creation
  - [ ] `async def get_subgraph(node_id: str, depth: int = 2) -> dict`: return ego-network for visualization
  - [ ] `async def health_check() -> bool`

- [ ] **10.2 — Community detection (`backend/src/graph/community_detection.py`)**
  - [ ] `async def run_louvain(tenant_id: UUID, min_community_size: int = 3) -> list[dict]`: project graph → run GDS Louvain → return communities with `{"community_id": int, "members": list[str], "size": int, "modularity": float}`
  - [ ] `async def run_label_propagation(tenant_id: UUID) -> list[dict]`: alternative algorithm for comparison
  - [ ] `async def detect_suspicious_communities(communities: list[dict]) -> list[dict]`: filter communities by suspicion heuristics:
    - Shared shipping addresses across multiple buyers
    - Same device fingerprint used by multiple accounts
    - Coordinated timing (>3 members transacting within 5 minutes)
    - Unusually high return/chargeback rates within the community

- [ ] **10.3 — Ring scorer (`backend/src/graph/ring_scorer.py`)**
  - [ ] `def score_ring(community: dict, transaction_stats: dict) -> float`: 0-1 suspicion score based on weighted heuristics (address sharing: 0.3, device sharing: 0.3, timing coordination: 0.2, chargeback rate: 0.2)
  - [ ] `def generate_ring_narrative(community: dict, score: float) -> str`: human-readable explanation of why this cluster is suspicious
  - [ ] `def format_for_alert(community: dict, score: float, narrative: str) -> AnomalyAlert`: create alert if score > 0.7

### Acceptance Criteria

- [ ] Neo4j constraints and indexes created successfully
- [ ] Batch node/edge creation handles 10,000 nodes without error
- [ ] Louvain detects synthetic planted communities (inject 3 connected buyers sharing an address)
- [ ] Ring scorer assigns score > 0.7 to communities with shared devices + addresses
- [ ] Subgraph extraction returns correct ego-network for visualization

### Verification Gate

```bash
cd backend && pytest tests/integration/test_graph_analysis.py -v
# Expected tests:
#   - test_batch_node_creation
#   - test_louvain_detects_planted_ring
#   - test_ring_scorer_flags_suspicious_cluster
#   - test_subgraph_extraction
```

**Sign-off:** Graph pipeline detects planted abuse rings with correct suspicion scores.

---

## Module 11: Observability & Monitoring

**Goal:** Wire up OpenTelemetry distributed tracing, Prometheus metrics, and Langfuse LLM tracing across all services — ensuring every request, model inference, and LLM call is observable.

### Key Files Created / Modified

- `backend/src/integrations/otel_setup.py`
- `backend/src/integrations/prometheus_metrics.py`
- `infra/docker/docker-compose.yml` (add Prometheus + Grafana)
- `infra/grafana/dashboards/risk_manager.json`

### Implementation Checklist

- [ ] **11.1 — OpenTelemetry setup (`backend/src/integrations/otel_setup.py`)**
  - [ ] Initialize `TracerProvider` with `BatchSpanProcessor` exporting to OTLP endpoint (Jaeger or Grafana Tempo)
  - [ ] Auto-instrument FastAPI via `FastAPIInstrumentor().instrument_app(app)`
  - [ ] Auto-instrument SQLAlchemy: `SQLAlchemyInstrumentor().instrument(engine=engine)`
  - [ ] Auto-instrument httpx: `HTTPXClientInstrumentor().instrument()`
  - [ ] Custom spans for: ML inference (`ml.inference`), agent steps (`agent.{step_name}`), Kafka produce/consume (`kafka.produce`, `kafka.consume`)

- [ ] **11.2 — Prometheus metrics (`backend/src/integrations/prometheus_metrics.py`)**
  - [ ] Define metrics:
    - `Histogram("return_scoring_latency_seconds", "Return scoring inference latency", buckets=[0.01, 0.025, 0.05, 0.1, 0.15, 0.3])`
    - `Histogram("chargeback_processing_duration_seconds", "Chargeback evidence assembly duration", buckets=[10, 30, 60, 120, 300])`
    - `Counter("requests_total", "Total API requests", ["method", "endpoint", "status_code"])`
    - `Counter("model_inferences_total", "Total model inferences", ["model_name", "model_version"])`
    - `Gauge("active_cases", "Currently active cases", ["source", "status"])`
    - `Gauge("kafka_consumer_lag", "Kafka consumer lag by topic", ["topic", "partition"])`
    - `Histogram("feature_staleness_seconds", "Feature cache staleness", ["feature_group"])`
    - `Counter("llm_tokens_total", "Total LLM tokens used", ["model", "direction"])`
    - `Counter("rate_limit_hits_total", "Rate limit rejections", ["endpoint"])`

- [ ] **11.3 — Grafana dashboards**
  - [ ] Create `infra/grafana/dashboards/risk_manager.json` with panels:
    - Return scoring latency (P50, P95, P99) — line chart
    - Request rate by endpoint — stacked area chart
    - Active cases by status — stacked bar chart
    - Model drift PSI values — gauge per feature
    - Kafka consumer lag — line chart per topic
    - Cost-weighted loss over time — line chart
    - LLM token usage and cost — counter
  - [ ] Add Grafana + Prometheus to `docker-compose.yml` with provisioned datasource and dashboard

- [ ] **11.4 — Langfuse integration verification**
  - [ ] Verify all LLM calls in agent pipeline create Langfuse generations with: prompt text, completion text, model name, token counts, latency
  - [ ] Verify Langfuse traces are created per chargeback case with all agent steps as spans
  - [ ] Verify Langfuse scores are recorded: evidence_completeness, win_probability

### Acceptance Criteria

- [ ] Distributed traces visible in Jaeger/Tempo showing full request lifecycle
- [ ] Prometheus `/metrics` endpoint returns all defined metrics
- [ ] Grafana dashboard loads with real data from dev environment
- [ ] Langfuse shows traced agent pipelines with token usage

### Verification Gate

```bash
# Process a return scoring request and verify trace
curl -X POST http://localhost:8000/api/v1/returns/score -d '...'
# Check Jaeger UI at http://localhost:16686 for trace
# Check Prometheus at http://localhost:9090 for metrics
curl -s http://localhost:8000/api/v1/metrics/prometheus | grep return_scoring_latency
# Check Grafana at http://localhost:3000 for dashboard
# Check Langfuse at http://localhost:3001 for LLM traces
```

**Sign-off:** Full observability stack operational — traces, metrics, and LLM traces all flowing.

---

## Module 12: Dashboard (Next.js Frontend)

**Goal:** Build the analyst-facing dashboard with real-time case management, chargeback review workflows, cost-weighted metrics visualization, and abuse-ring graph rendering.

### Key Files Created / Modified

- `dashboard/src/app/layout.tsx`
- `dashboard/src/app/page.tsx`
- `dashboard/src/app/chargebacks/page.tsx`
- `dashboard/src/app/chargebacks/[id]/page.tsx`
- `dashboard/src/app/returns/page.tsx`
- `dashboard/src/app/fraud/page.tsx`
- `dashboard/src/app/rings/page.tsx`
- `dashboard/src/app/evaluation/page.tsx`
- `dashboard/src/app/settings/page.tsx`
- `dashboard/src/components/ui/*`
- `dashboard/src/components/charts/*`
- `dashboard/src/components/case-review/*`
- `dashboard/src/components/graph-viz/*`
- `dashboard/src/lib/api-client.ts`
- `dashboard/src/hooks/use-cases.ts`
- `dashboard/src/hooks/use-metrics.ts`

### Implementation Checklist

- [ ] **12.1 — API client (`dashboard/src/lib/api-client.ts`)**
  - [ ] Typed `fetch` wrapper with JWT token management (stored in httpOnly cookie)
  - [ ] Auto-refresh token on 401
  - [ ] Methods for all API endpoints: `scorReturn()`, `ingestChargeback()`, `listCases()`, `reviewChargeback()`, `getStats()`, `getEvaluationReport()`, etc.
  - [ ] Error handling: parse API error responses into typed error objects

- [ ] **12.2 — Root layout (`dashboard/src/app/layout.tsx`)**
  - [ ] Dark mode sidebar navigation with links: Dashboard, Chargebacks, Returns, Fraud Alerts, Abuse Rings, Model Evaluation, Settings
  - [ ] Top bar with: tenant name, user avatar, notification bell (count of pending reviews + deadline warnings)
  - [ ] CSS design system using CSS custom properties: colors (dark palette), spacing, border-radius, typography (Inter font from Google Fonts)

- [ ] **12.3 — Dashboard home (`dashboard/src/app/page.tsx`)**
  - [ ] KPI cards row: Total Active Cases, Chargeback Win Rate (last 90d), Total ₹ Saved, Pending Reviews, Approaching Deadlines
  - [ ] Cost-weighted metrics chart: line chart of precision, recall, cost-weighted loss over time (Recharts)
  - [ ] Case distribution: donut chart by source (chargeback, return, fraud, ring)
  - [ ] Recent activity feed: latest case updates, alerts, model evaluations

- [ ] **12.4 — Chargeback pages**
  - [ ] List page (`chargebacks/page.tsx`): sortable table with columns: Case ID, ARN, Network, Reason Code, Amount, Status, Deadline, Win Probability, Assigned To. Filters: status dropdown, network dropdown, date range. Pagination
  - [ ] Detail page (`chargebacks/[id]/page.tsx`):
    - Case header: status badge, deadline countdown (color-coded: green >7d, yellow 3-7d, red <3d)
    - Evidence panel: list of `EvidenceItem`s with status icons (found/missing)
    - Narrative panel: rendered draft with edit-in-place capability
    - Confidence panel: win probability gauge, SHAP feature chart (horizontal bar chart)
    - Similar cases panel: list of top-5 similar historical cases with outcomes
    - Review actions: Approve, Edit, Reject buttons with confirmation dialogs
    - Audit trail: timeline of all actions on this case

- [ ] **12.5 — Returns page (`dashboard/src/app/returns/page.tsx`)**
  - [ ] Risk score distribution: histogram of recent scores
  - [ ] Decision breakdown: pie chart of auto_approve / manual_review / auto_deny
  - [ ] Recent decisions table: Customer ID, Order Amount, Risk Score, Tier, Decision, Top Features
  - [ ] Policy config panel: editable thresholds with save button

- [ ] **12.6 — Fraud alerts page (`dashboard/src/app/fraud/page.tsx`)**
  - [ ] Active alerts list with severity color-coding
  - [ ] Alert detail: TPS chart (baseline vs. current), geographic heatmap, transaction list
  - [ ] Registered events calendar

- [ ] **12.7 — Abuse rings page (`dashboard/src/app/rings/page.tsx`)**
  - [ ] Force-directed graph visualization (D3.js) showing detected communities
  - [ ] Node coloring by entity type (buyer=blue, seller=green, device=orange, address=purple)
  - [ ] Edge thickness by transaction volume
  - [ ] Click on community to expand and see member details + suspicion score

- [ ] **12.8 — Evaluation page (`dashboard/src/app/evaluation/page.tsx`)**
  - [ ] Model selector dropdown (return_risk, chargeback_win, fraud_spike)
  - [ ] Latest evaluation report: metrics table, ROC curve, calibration curve, threshold sweep chart
  - [ ] Champion vs. challenger comparison table
  - [ ] Drift report: per-feature PSI values with color-coded status (green < 0.1, yellow 0.1-0.2, red > 0.2)
  - [ ] Evaluation history: list of past runs with metrics trends

- [ ] **12.9 — Settings page (`dashboard/src/app/settings/page.tsx`)**
  - [ ] Tenant configuration: name, API key regeneration
  - [ ] Notification channels: configure Slack webhook URL, email recipients per severity level
  - [ ] Policy configuration: threshold sliders for return scoring
  - [ ] User management: list users, invite new user, assign roles (RBAC)
  - [ ] Data retention settings: display current retention policy

### Acceptance Criteria

- [ ] Dashboard renders correctly in Chrome and Firefox
- [ ] All pages load data from backend API
- [ ] Chargeback review workflow (approve/edit/reject) completes successfully
- [ ] Graph visualization renders detected communities with correct node/edge relationships
- [ ] Evaluation charts display correct metrics from evaluation reports
- [ ] Real-time updates: new cases appear without page refresh (SSE or polling)
- [ ] Responsive layout works on 1280px+ screens (primary analyst use case)

### Verification Gate

```bash
cd dashboard && npm run build  # verify no build errors
cd dashboard && npm run lint   # verify no lint errors
# Manual verification (or Playwright e2e tests):
#   - Navigate to /chargebacks → table loads with data
#   - Click a case → detail page renders evidence, narrative, confidence
#   - Click Approve → status changes to SUBMITTED
#   - Navigate to /evaluation → charts render with metrics
#   - Navigate to /rings → graph visualization renders
```

**Sign-off:** Dashboard builds without errors, all pages render data, review workflow completes end-to-end.

---

## Module 13: End-to-End Integration Testing

**Goal:** Validate the complete system flow from external webhook → ingestion → processing → ML scoring → agent pipeline → analyst review → outcome tracking, ensuring all modules work together correctly.

### Key Files Created / Modified

- `backend/tests/integration/test_e2e_chargeback_flow.py`
- `backend/tests/integration/test_e2e_return_scoring_flow.py`
- `backend/tests/integration/test_e2e_fraud_detection_flow.py`
- `backend/tests/integration/test_e2e_evaluation_flow.py`

### Implementation Checklist

- [ ] **13.1 — Chargeback end-to-end test**
  - [ ] Test: `test_chargeback_full_lifecycle`:
    1. `POST /v1/chargebacks/ingest` with valid Visa chargeback notification
    2. Assert: case created with status `NEW`, deadline = received_at + 30d
    3. Wait for agent pipeline to complete (poll case status)
    4. Assert: status transitions through `EVIDENCE_GATHERING` → `DRAFT_READY`
    5. Assert: evidence bundle populated with items
    6. Assert: narrative draft generated (non-empty, contains required sections)
    7. Assert: win probability in [0, 1]
    8. `POST /v1/chargebacks/{case_id}/review` with action `approve`
    9. Assert: status → `SUBMITTED`, audit log entry created
    10. Assert: Langfuse trace exists with all agent steps
    11. Assert: Prometheus metrics updated (chargeback_processing_duration)

- [ ] **13.2 — Duplicate chargeback rejection test**
  - [ ] `POST /v1/chargebacks/ingest` with same ARN twice
  - [ ] Assert: first → 202, second → 409 with `DuplicateIngestionError`

- [ ] **13.3 — Return scoring end-to-end test**
  - [ ] `POST /v1/returns/score` with valid request
  - [ ] Assert: response within 300ms
  - [ ] Assert: risk_score in [0, 100], risk_tier matches score, decision matches tier + policy
  - [ ] Assert: top_features has 5 items with SHAP values
  - [ ] Assert: decision record persisted in PostgreSQL
  - [ ] Assert: ReturnEvent published to Kafka

- [ ] **13.4 — Return scoring degraded mode test**
  - [ ] Stop Redis container
  - [ ] `POST /v1/returns/score` with valid request
  - [ ] Assert: response still returned (degraded mode), `is_degraded` flag may not be in API response but logged
  - [ ] Assert: response within 500ms (relaxed for degraded mode)
  - [ ] Start Redis container again

- [ ] **13.5 — Fraud detection end-to-end test**
  - [ ] Publish 100 transactions to `transactions.raw` within 1 second (simulating spike)
  - [ ] Assert: anomaly alert appears in `alerts.outbound` topic
  - [ ] Assert: alert visible via `GET /v1/fraud/alerts`
  - [ ] Assert: case created with source `FRAUD_ALERT`

- [ ] **13.6 — Evaluation pipeline end-to-end test**
  - [ ] Trigger evaluation via `python scripts/run_evaluation.py`
  - [ ] Assert: evaluation report created in PostgreSQL
  - [ ] Assert: report uploaded to MinIO/S3
  - [ ] Assert: metrics visible via `GET /v1/metrics/evaluation/return_risk/latest`
  - [ ] Assert: cost_weighted_loss computed correctly

- [ ] **13.7 — Cross-cutting verification**
  - [ ] Assert: all API responses include `X-Request-ID` header
  - [ ] Assert: rate limiting works across all endpoints
  - [ ] Assert: RLS prevents tenant A from seeing tenant B's data
  - [ ] Assert: audit logs created for all state-changing operations

### Acceptance Criteria

- [ ] All e2e tests pass with a fully running Docker Compose stack
- [ ] No data leaks between tenants
- [ ] System handles graceful degradation (Redis down, LLM timeout)
- [ ] All latency budgets met under normal conditions

### Verification Gate

```bash
# Start full stack
make up
cd backend && alembic upgrade head
cd backend && python scripts/seed_db.py
cd backend && faust -A src.streaming.app worker -l info &

# Run all e2e tests
cd backend && pytest tests/integration/test_e2e_*.py -v --tb=long -x
# Expected: ALL tests pass

# Verify observability
# Check Jaeger: traces for all e2e test requests
# Check Prometheus: metrics updated
# Check Langfuse: traces for chargeback agent pipeline

make down
```

**Sign-off:** All 7 end-to-end tests pass on a full Docker Compose stack. System handles degradation gracefully. All observability data flowing. Zero cross-tenant data leaks.

---

## Final Checklist: Production Readiness

- [ ] All 13 modules completed with passing verification gates
- [ ] `pytest tests/ -v --cov=src --cov-fail-under=80` — coverage ≥ 80%
- [ ] `ruff check src/ tests/` — zero lint errors
- [ ] `mypy src/` — zero type errors
- [ ] `npm run build` (dashboard) — zero build errors
- [ ] Docker images build successfully for all 3 services
- [ ] `.env.example` documents all required environment variables
- [ ] OpenAPI spec auto-generated at `/docs` with all endpoints documented
- [ ] README.md updated with: setup instructions, architecture overview, development guide
- [ ] All ADRs (Architecture Decision Records) written for key decisions in `docs/architecture/decisions/`
- [ ] Model evaluation report demonstrates measured precision, recall, and cost-weighted loss on held-out test set (core problem statement requirement)
- [ ] Defense-only constraint verified: no endpoint allows fraud generation, synthetic identity creation, or adversarial example generation
