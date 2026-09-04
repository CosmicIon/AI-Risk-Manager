"""
Module: Real-Time Fraud Scoring Microservice (FastAPI)
Provides high-throughput, sub-50ms inference, enterprise 3-tier risk triage,
explainability reason codes, and operational telemetry.
"""

from collections import deque
from contextlib import asynccontextmanager
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
import joblib
import numpy as np
import pandas as pd
from pydantic import BaseModel, Field

from src.utils import get_project_root, load_config


# ---------------------------------------------------------------------------
# Pydantic Schemas
# ---------------------------------------------------------------------------
class TransactionRequest(BaseModel):
    transaction_id: int = Field(..., description="Unique transaction ID", json_schema_extra={"example": 1058291})
    customer_id: int = Field(..., description="Customer account identifier", json_schema_extra={"example": 24})
    terminal_id: int = Field(..., description="POS or virtual terminal identifier", json_schema_extra={"example": 42})
    tx_amount: float = Field(..., gt=0, description="Transaction monetary amount", json_schema_extra={"example": 340.50})
    tx_datetime: Optional[str] = Field(
        default=None,
        description="ISO 8601 transaction timestamp (defaults to current time)",
        json_schema_extra={"example": "2026-09-04T14:32:00"},
    )


class BatchTransactionRequest(BaseModel):
    transactions: List[TransactionRequest] = Field(..., max_length=100)


class RiskEvaluationResponse(BaseModel):
    transaction_id: int
    risk_score: float
    decision: str = Field(..., description="3-Tier Triage Action: APPROVE | CHALLENGE | DECLINE")
    latency_ms: float
    reasons: List[str]
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    features_count: int
    version: str
    uptime_seconds: float


class MetricsResponse(BaseModel):
    total_requests: int
    avg_latency_ms: float
    p95_latency_ms: float
    decisions: Dict[str, int]


# ---------------------------------------------------------------------------
# In-Memory Feature Store & Context Cache
# ---------------------------------------------------------------------------
class InMemoryFeatureStore:
    """
    In-memory feature cache that preloads customer/terminal profiles and rolling statistics
    to enable single-digit millisecond feature generation without database lookups.
    """

    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.cust_profiles: Dict[int, Dict[str, Any]] = {}
        self.term_profiles: Dict[int, Dict[str, Any]] = {}
        self.cust_rolling_stats: Dict[int, Dict[str, Any]] = {}
        self.term_rolling_stats: Dict[int, Dict[str, Any]] = {}
        self.global_defaults: Dict[str, float] = {}
        self.load_stores()

    def load_stores(self):
        raw_dir = self.root_dir / "data" / "raw"
        proc_dir = self.root_dir / "data" / "processed"

        # 1. Load customer profiles
        cust_pkl = raw_dir / "customer_profiles.pkl"
        if cust_pkl.exists():
            cdf = pd.read_pickle(cust_pkl)
            for _, r in cdf.iterrows():
                cid = int(r["CUSTOMER_ID"])
                self.cust_profiles[cid] = {
                    "x": float(r.get("x_customer_id", 50.0)),
                    "y": float(r.get("y_customer_id", 50.0)),
                    "mean_amount": float(r.get("mean_amount", 50.0)),
                    "std_amount": float(r.get("std_amount", 20.0)),
                    "mean_nb_tx_per_day": float(r.get("mean_nb_tx_per_day", 2.0)),
                }

        # 2. Load terminal profiles
        term_pkl = raw_dir / "terminal_profiles.pkl"
        if term_pkl.exists():
            tdf = pd.read_pickle(term_pkl)
            for _, r in tdf.iterrows():
                tid = int(r["TERMINAL_ID"])
                self.term_profiles[tid] = {
                    "x": float(r.get("x_terminal_id", 50.0)),
                    "y": float(r.get("y_terminal_id", 50.0)),
                }

        # 3. Cache rolling statistics from processed features if available
        feat_path = proc_dir / "features.parquet"
        if feat_path.exists():
            df = pd.read_parquet(feat_path)
            # Latest terminal risks
            latest_term = df.sort_values("TX_DATETIME").groupby("TERMINAL_ID").last()
            for tid, r in latest_term.iterrows():
                self.term_rolling_stats[int(tid)] = {
                    "risk_1d": float(r.get("TERMINAL_ID_RISK_1DAY_WINDOW", 0.0)),
                    "risk_7d": float(r.get("TERMINAL_ID_RISK_7DAY_WINDOW", 0.0)),
                    "risk_30d": float(r.get("TERMINAL_ID_RISK_30DAY_WINDOW", 0.0)),
                    "nb_1d": float(r.get("TERMINAL_ID_NB_TX_1DAY_WINDOW", 1.0)),
                    "nb_7d": float(r.get("TERMINAL_ID_NB_TX_7DAY_WINDOW", 7.0)),
                    "nb_30d": float(r.get("TERMINAL_ID_NB_TX_30DAY_WINDOW", 30.0)),
                }

            # Latest customer metrics
            latest_cust = df.sort_values("TX_DATETIME").groupby("CUSTOMER_ID").last()
            for cid, r in latest_cust.iterrows():
                self.cust_rolling_stats[int(cid)] = {
                    "avg_1d": float(r.get("CUSTOMER_ID_AVG_AMOUNT_1DAY_WINDOW", 50.0)),
                    "avg_7d": float(r.get("CUSTOMER_ID_AVG_AMOUNT_7DAY_WINDOW", 50.0)),
                    "avg_30d": float(r.get("CUSTOMER_ID_AVG_AMOUNT_30DAY_WINDOW", 50.0)),
                    "std_30d": float(r.get("CUSTOMER_ID_STD_AMOUNT_30DAY_WINDOW", 20.0)),
                    "nb_15min": float(r.get("CUSTOMER_ID_NB_TX_15MIN_WINDOW", 0.0)),
                    "nb_1h": float(r.get("CUSTOMER_ID_NB_TX_1HOUR_WINDOW", 0.0)),
                    "nb_1d": float(r.get("CUSTOMER_ID_NB_TX_1DAY_WINDOW", 1.0)),
                    "nb_7d": float(r.get("CUSTOMER_ID_NB_TX_7DAY_WINDOW", 5.0)),
                    "nb_30d": float(r.get("CUSTOMER_ID_NB_TX_30DAY_WINDOW", 20.0)),
                    "time_since_last": float(r.get("TIME_SINCE_LAST_TX", 43200.0)),
                }

        self.global_defaults = {
            "mean_amount": 55.0,
            "std_amount": 25.0,
            "distance": 25.0,
            "time_since_last": 43200.0,
        }

    def extract_features(
        self, req: TransactionRequest, feature_cols: List[str]
    ) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Builds the single-transaction feature vector aligned with feature_cols.
        Returns (DataFrame, context_dict).
        """
        if req.tx_datetime:
            try:
                dt = datetime.fromisoformat(req.tx_datetime)
            except Exception:
                dt = datetime.now(timezone.utc)
        else:
            dt = datetime.now(timezone.utc)

        is_weekend = 1 if dt.weekday() >= 5 else 0
        is_night = 1 if dt.hour < 6 else 0

        # Customer & Terminal profile lookup
        cust_prof = self.cust_profiles.get(req.customer_id, {})
        term_prof = self.term_profiles.get(req.terminal_id, {})
        cust_stats = self.cust_rolling_stats.get(req.customer_id, {})
        term_stats = self.term_rolling_stats.get(req.terminal_id, {})

        # Coordinate distance
        if cust_prof and term_prof:
            dist = np.sqrt(
                (cust_prof["x"] - term_prof["x"]) ** 2 + (cust_prof["y"] - term_prof["y"]) ** 2
            )
        else:
            dist = self.global_defaults["distance"]

        # Customer baseline statistics
        avg_30d = cust_stats.get("avg_30d", cust_prof.get("mean_amount", self.global_defaults["mean_amount"]))
        std_30d = cust_stats.get("std_30d", cust_prof.get("std_amount", self.global_defaults["std_amount"]))
        z_score = (req.tx_amount - avg_30d) / (std_30d + 1.0)

        feature_map = {
            "TX_AMOUNT": req.tx_amount,
            "TX_DURING_WEEKEND": is_weekend,
            "TX_DURING_NIGHT": is_night,
            "TX_DIST_CUSTOMER_TERMINAL": float(dist),
            "CUSTOMER_ID_NB_TX_15MIN_WINDOW": float(cust_stats.get("nb_15min", 0.0)),
            "CUSTOMER_ID_NB_TX_1HOUR_WINDOW": float(cust_stats.get("nb_1h", 0.0)),
            "TIME_SINCE_LAST_TX": float(cust_stats.get("time_since_last", self.global_defaults["time_since_last"])),
            "CUSTOMER_ID_NB_TX_1DAY_WINDOW": float(cust_stats.get("nb_1d", 1.0)),
            "CUSTOMER_ID_AVG_AMOUNT_1DAY_WINDOW": float(cust_stats.get("avg_1d", avg_30d)),
            "CUSTOMER_ID_NB_TX_7DAY_WINDOW": float(cust_stats.get("nb_7d", 5.0)),
            "CUSTOMER_ID_AVG_AMOUNT_7DAY_WINDOW": float(cust_stats.get("avg_7d", avg_30d)),
            "CUSTOMER_ID_NB_TX_30DAY_WINDOW": float(cust_stats.get("nb_30d", 20.0)),
            "CUSTOMER_ID_AVG_AMOUNT_30DAY_WINDOW": float(avg_30d),
            "CUSTOMER_ID_STD_AMOUNT_30DAY_WINDOW": float(std_30d),
            "TX_AMOUNT_ZSCORE": float(z_score),
            "TERMINAL_ID_NB_TX_1DAY_WINDOW": float(term_stats.get("nb_1d", 1.0)),
            "TERMINAL_ID_RISK_1DAY_WINDOW": float(term_stats.get("risk_1d", 0.0)),
            "TERMINAL_ID_NB_TX_7DAY_WINDOW": float(term_stats.get("nb_7d", 5.0)),
            "TERMINAL_ID_RISK_7DAY_WINDOW": float(term_stats.get("risk_7d", 0.0)),
            "TERMINAL_ID_NB_TX_30DAY_WINDOW": float(term_stats.get("nb_30d", 25.0)),
            "TERMINAL_ID_RISK_30DAY_WINDOW": float(term_stats.get("risk_30d", 0.0)),
        }

        # Align to model feature column ordering
        ordered_data = {col: [feature_map.get(col, 0.0)] for col in feature_cols}
        feature_df = pd.DataFrame(ordered_data)

        context = {
            "avg_30d": avg_30d,
            "std_30d": std_30d,
            "z_score": z_score,
            "distance": dist,
            "is_night": is_night,
            "terminal_risk_7d": term_stats.get("risk_7d", 0.0),
            "velocity_15min": cust_stats.get("nb_15min", 0.0),
        }

        return feature_df, context


# ---------------------------------------------------------------------------
# Global State & Lifespan
# ---------------------------------------------------------------------------
class AppState:
    def __init__(self):
        self.model = None
        self.feature_cols: List[str] = []
        self.feature_store: Optional[InMemoryFeatureStore] = None
        self.start_time: float = time.time()
        self.latencies: deque = deque(maxlen=1000)
        self.decision_counts = {"APPROVE": 0, "CHALLENGE": 0, "DECLINE": 0}
        self.thresh_challenge = 0.30
        self.thresh_decline = 0.78


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load ML assets & in-memory caches
    root = get_project_root()
    models_dir = root / "models"
    model_path = models_dir / "model.pkl"
    feats_path = models_dir / "feature_columns.json"

    if model_path.exists():
        state.model = joblib.load(model_path)
    if feats_path.exists():
        with open(feats_path, "r") as f:
            state.feature_cols = json.load(f)

    # Initialize feature store
    state.feature_store = InMemoryFeatureStore(root)

    # Load dynamic thresholds from config if available
    config = load_config()
    eval_cfg = config.get("evaluation", {})
    state.thresh_challenge = float(eval_cfg.get("threshold_challenge", 0.30))
    state.thresh_decline = float(eval_cfg.get("threshold_decline", 0.78))
    state.start_time = time.time()

    yield


# ---------------------------------------------------------------------------
# FastAPI App Definition
# ---------------------------------------------------------------------------
app = FastAPI(
    title="AI Risk Manager: Real-Time Scoring API",
    description="Synchronous low-latency transaction risk evaluation microservice with 3-tier triage and explainability.",
    version="2.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def generate_reason_codes(
    req: TransactionRequest, risk_score: float, context: Dict[str, Any], decision: str
) -> List[str]:
    """Generates human-readable compliance/analyst reason codes for the decision."""
    reasons = []

    if decision == "APPROVE":
        reasons.append("Risk score within normal statistical baseline.")
        return reasons

    # Anomaly explanations
    avg_30d = context["avg_30d"]
    ratio = req.tx_amount / (avg_30d + 0.01)
    if ratio >= 2.5:
        reasons.append(
            f"Transaction amount (${req.tx_amount:.2f}) is {ratio:.1f}x higher than 30-day baseline (${avg_30d:.2f})."
        )

    if context["z_score"] >= 3.0:
        reasons.append(f"High spending deviation: Z-score is +{context['z_score']:.2f} standard deviations.")

    if context["distance"] >= 45.0:
        reasons.append(
            f"Geographic anomaly: Terminal is {context['distance']:.1f} units away from customer anchor."
        )

    if context["terminal_risk_7d"] >= 0.20:
        reasons.append(
            f"Terminal elevated risk: 7-day terminal fraud probability is {context['terminal_risk_7d']*100:.1f}%."
        )

    if context["velocity_15min"] >= 2:
        reasons.append(f"Velocity burst: Multiple transactions detected within 15 minutes.")

    if context["is_night"] == 1:
        reasons.append("Off-hours transaction initiated during high-risk night window (00:00 - 06:00).")

    if not reasons:
        reasons.append("Elevated multivariate risk detected across customer spending patterns.")

    return reasons


def evaluate_single_transaction(req: TransactionRequest) -> RiskEvaluationResponse:
    """Core evaluation pipeline for a single transaction request."""
    t0 = time.perf_counter()

    if state.model is None or state.feature_store is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Risk scoring model or feature store not loaded.",
        )

    # 1. Real-time feature synthesis
    feature_df, context = state.feature_store.extract_features(req, state.feature_cols)

    # 2. Model inference
    proba = float(state.model.predict_proba(feature_df)[0, 1])

    # 3. 3-Tier Triage Routing
    if proba < state.thresh_challenge:
        decision = "APPROVE"
    elif proba < state.thresh_decline:
        decision = "CHALLENGE"
    else:
        decision = "DECLINE"

    # 4. Reason codes
    reasons = generate_reason_codes(req, proba, context, decision)

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)

    # Telemetry updates
    state.latencies.append(latency_ms)
    state.decision_counts[decision] += 1

    return RiskEvaluationResponse(
        transaction_id=req.transaction_id,
        risk_score=round(proba, 4),
        decision=decision,
        latency_ms=latency_ms,
        reasons=reasons,
        timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    )


# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@app.get("/", tags=["Info"])
def root_info():
    return {
        "service": "AI Risk Manager Scoring Microservice",
        "version": "2.1.0",
        "docs_url": "/docs",
        "health_url": "/health",
        "metrics_url": "/metrics",
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check():
    return HealthResponse(
        status="healthy" if state.model is not None else "degraded",
        model_loaded=state.model is not None,
        features_count=len(state.feature_cols),
        version="v2.1",
        uptime_seconds=round(time.time() - state.start_time, 1),
    )


@app.get("/metrics", response_model=MetricsResponse, tags=["Observability"])
def get_metrics():
    latencies = list(state.latencies)
    avg_lat = float(np.mean(latencies)) if latencies else 0.0
    p95_lat = float(np.percentile(latencies, 95)) if latencies else 0.0
    total = sum(state.decision_counts.values())

    return MetricsResponse(
        total_requests=total,
        avg_latency_ms=round(avg_lat, 2),
        p95_latency_ms=round(p95_lat, 2),
        decisions=state.decision_counts,
    )


@app.post(
    "/v1/risk/evaluate",
    response_model=RiskEvaluationResponse,
    status_code=status.HTTP_200_OK,
    tags=["Inference"],
)
def evaluate_transaction(request: TransactionRequest):
    """
    Evaluates a single payment transaction in real time (<50ms).
    Returns risk probability, 3-tier triage routing, and explainability reasons.
    """
    return evaluate_single_transaction(request)


@app.post(
    "/v1/risk/evaluate/batch",
    response_model=List[RiskEvaluationResponse],
    status_code=status.HTTP_200_OK,
    tags=["Inference"],
)
def evaluate_batch_transactions(request: BatchTransactionRequest):
    """
    Micro-batch evaluation for up to 100 transactions in a single payload.
    """
    return [evaluate_single_transaction(tx) for tx in request.transactions]


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.api:app", host="0.0.0.0", port=8000, reload=True)
