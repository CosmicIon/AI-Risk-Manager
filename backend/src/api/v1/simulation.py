"""Simulation Studio API — generate datasets, stream transactions, and visualize results."""

from __future__ import annotations

import asyncio
import json
import logging
import os
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

import numpy as np
import pandas as pd
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.core.schemas.simulation import (
    ScenarioBreakdown,
    SimulatedTransaction,
    SimulationConfig,
    SimulationStats,
    StreamConfig,
)
from src.ml.simulation.generator import generate_complete_dataset

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/simulation", tags=["simulation"])

# ── Module-level state ───────────────────────────────────────────────────────

_executor = ThreadPoolExecutor(max_workers=2)

# In-memory references for streaming
_stream_task: asyncio.Task | None = None
_stream_running = False
_websocket_clients: set[WebSocket] = set()

# Cached dataset for streaming (loaded after generation)
_cached_tx_df: pd.DataFrame | None = None

# Data output directory
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "synthetic")


# ── Helpers ──────────────────────────────────────────────────────────────────


def _run_generation(config: SimulationConfig) -> dict:
    """Run dataset generation in a thread pool (CPU-bound work)."""
    tx_df, customers_df, terminals_df = generate_complete_dataset(config)

    # Ensure output directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    holdout_dir = os.path.join(DATA_DIR, "holdout")
    os.makedirs(holdout_dir, exist_ok=True)

    # Time-based 80/20 split
    split_idx = int(len(tx_df) * 0.8)
    train_df = tx_df.iloc[:split_idx]
    holdout_df = tx_df.iloc[split_idx:]

    # Save Parquet files
    train_df.to_parquet(os.path.join(DATA_DIR, "transactions.parquet"), index=False)
    holdout_df.to_parquet(os.path.join(holdout_dir, "transactions.parquet"), index=False)
    customers_df.to_parquet(os.path.join(DATA_DIR, "customers.parquet"), index=False)
    terminals_df.to_parquet(os.path.join(DATA_DIR, "terminals.parquet"), index=False)

    logger.info("Saved dataset to %s (train=%d, holdout=%d)", DATA_DIR, len(train_df), len(holdout_df))

    # Compute statistics
    fraud_mask = tx_df["tx_fraud"] == 1
    fraud_amounts = tx_df.loc[fraud_mask, "tx_amount"]

    scenario_counts = tx_df["tx_fraud_scenario"].value_counts().to_dict()

    # Customer and terminal coordinate data for spatial visualization
    customer_coords = customers_df[["customer_id", "x_customer", "y_customer"]].rename(
        columns={"x_customer": "x", "y_customer": "y"}
    ).to_dict("records")

    terminal_coords = terminals_df[["terminal_id", "x_terminal", "y_terminal", "mcc"]].rename(
        columns={"x_terminal": "x", "y_terminal": "y"}
    ).to_dict("records")

    # Identify currently compromised terminals/customers (from Scenario 2/3)
    compromised_terminals = (
        tx_df.loc[tx_df["tx_fraud_scenario"] == 2, "terminal_id"].unique().tolist()
    )
    compromised_customers = (
        tx_df.loc[tx_df["tx_fraud_scenario"] == 3, "customer_id"].unique().tolist()
    )

    stats = {
        "total_transactions": len(tx_df),
        "total_customers": len(customers_df),
        "total_terminals": len(terminals_df),
        "nb_days": config.nb_days,
        "fraud_count": int(fraud_mask.sum()),
        "fraud_rate": round(float(fraud_mask.mean()), 6),
        "scenario_breakdown": {
            "scenario_0_legitimate": int(scenario_counts.get(0, 0)),
            "scenario_1_high_amount": int(scenario_counts.get(1, 0)),
            "scenario_2_compromised_terminal": int(scenario_counts.get(2, 0)),
            "scenario_3_account_takeover": int(scenario_counts.get(3, 0)),
        },
        "total_loss_inr": round(float(fraud_amounts.sum()), 2) if len(fraud_amounts) > 0 else 0.0,
        "train_count": len(train_df),
        "holdout_count": len(holdout_df),
        "avg_amount": round(float(tx_df["tx_amount"].mean()), 2),
        "median_amount": round(float(tx_df["tx_amount"].median()), 2),
        "generated_at": datetime.now().isoformat(),
        "customer_coordinates": customer_coords,
        "terminal_coordinates": terminal_coords,
        "compromised_terminals": compromised_terminals,
        "compromised_customers": compromised_customers,
    }

    # Store full tx_df for streaming
    return {"stats": stats, "tx_df_json": tx_df.to_json(orient="records", date_format="iso")}


def _compute_mock_ml_score(tx: dict) -> float:
    """Compute a naive simulated ML risk score for demonstration.

    This intentionally imperfect scorer creates realistic gaps between
    ground truth and model predictions for the dashboard to visualize.
    """
    amount = tx.get("tx_amount", 0)
    fraud = tx.get("tx_fraud", 0)

    # Base score from amount (higher amounts → higher risk)
    base_score = min(1.0, amount / 30000.0)

    # Add noise
    noise = np.random.uniform(-0.15, 0.15)

    # Boost if actually fraud (but not perfectly)
    if fraud == 1:
        score = min(1.0, base_score + 0.3 + noise)
    else:
        score = max(0.0, min(1.0, base_score * 0.4 + noise))

    return round(float(score), 4)


# ── Endpoints ────────────────────────────────────────────────────────────────


@router.post("/generate", response_model=SimulationStats)
async def generate_dataset(config: SimulationConfig):
    """Generate a complete Handbook-compliant simulated dataset.

    Runs the simulation engine in a thread pool, saves Parquet files to
    data/synthetic/ with 80/20 time-split, and returns statistical summary.
    """
    global _cached_tx_df

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(_executor, _run_generation, config)

    # Cache for streaming
    _cached_tx_df = pd.read_json(result["tx_df_json"], orient="records")

    stats = result["stats"]
    return SimulationStats(**stats)


class StatsResponse(BaseModel):
    """Response for /stats endpoint when no data exists yet."""

    status: str
    message: str


@router.get("/stats")
async def get_stats():
    """Return current dataset distributions for visualization.

    Reads from the latest generated Parquet files in data/synthetic/.
    """
    tx_path = os.path.join(DATA_DIR, "transactions.parquet")
    cust_path = os.path.join(DATA_DIR, "customers.parquet")
    term_path = os.path.join(DATA_DIR, "terminals.parquet")

    if not os.path.exists(tx_path):
        return {"status": "empty", "message": "No dataset generated yet. Use POST /simulation/generate first."}

    tx_df = pd.read_parquet(tx_path)
    customers_df = pd.read_parquet(cust_path) if os.path.exists(cust_path) else pd.DataFrame()
    terminals_df = pd.read_parquet(term_path) if os.path.exists(term_path) else pd.DataFrame()

    fraud_mask = tx_df["tx_fraud"] == 1
    scenario_counts = tx_df["tx_fraud_scenario"].value_counts().to_dict()

    customer_coords = []
    if not customers_df.empty:
        customer_coords = customers_df[["customer_id", "x_customer", "y_customer"]].rename(
            columns={"x_customer": "x", "y_customer": "y"}
        ).to_dict("records")

    terminal_coords = []
    if not terminals_df.empty:
        terminal_coords = terminals_df[["terminal_id", "x_terminal", "y_terminal", "mcc"]].rename(
            columns={"x_terminal": "x", "y_terminal": "y"}
        ).to_dict("records")

    compromised_terminals = tx_df.loc[tx_df["tx_fraud_scenario"] == 2, "terminal_id"].unique().tolist()
    compromised_customers = tx_df.loc[tx_df["tx_fraud_scenario"] == 3, "customer_id"].unique().tolist()

    return SimulationStats(
        total_transactions=len(tx_df),
        total_customers=len(customers_df),
        total_terminals=len(terminals_df),
        nb_days=int(tx_df["tx_time_days"].max()) + 1 if "tx_time_days" in tx_df.columns else 0,
        fraud_count=int(fraud_mask.sum()),
        fraud_rate=round(float(fraud_mask.mean()), 6),
        scenario_breakdown=ScenarioBreakdown(
            scenario_0_legitimate=int(scenario_counts.get(0, 0)),
            scenario_1_high_amount=int(scenario_counts.get(1, 0)),
            scenario_2_compromised_terminal=int(scenario_counts.get(2, 0)),
            scenario_3_account_takeover=int(scenario_counts.get(3, 0)),
        ),
        total_loss_inr=round(float(tx_df.loc[fraud_mask, "tx_amount"].sum()), 2),
        train_count=len(tx_df),
        holdout_count=0,
        avg_amount=round(float(tx_df["tx_amount"].mean()), 2),
        median_amount=round(float(tx_df["tx_amount"].median()), 2),
        generated_at=datetime.now(),
        customer_coordinates=customer_coords,
        terminal_coordinates=terminal_coords,
        compromised_terminals=compromised_terminals,
        compromised_customers=compromised_customers,
    )


@router.post("/stream/start")
async def start_stream(config: StreamConfig = StreamConfig()):
    """Start streaming transactions in real time to WebSocket clients.

    Streams from the cached dataset at the configured TPS rate.
    If Kafka is available, also publishes to 'transactions.raw' topic.
    """
    global _stream_task, _stream_running, _cached_tx_df

    if _stream_running:
        return {"status": "already_running", "message": "Stream is already active."}

    if _cached_tx_df is None or _cached_tx_df.empty:
        # Try loading from disk
        tx_path = os.path.join(DATA_DIR, "transactions.parquet")
        if os.path.exists(tx_path):
            _cached_tx_df = pd.read_parquet(tx_path)
        else:
            return {"status": "error", "message": "No dataset available. Generate one first."}

    _stream_running = True
    _stream_task = asyncio.create_task(_stream_loop(config))

    return {"status": "started", "tps_rate": config.tps_rate, "total_transactions": len(_cached_tx_df)}


@router.post("/stream/stop")
async def stop_stream():
    """Stop the live transaction stream."""
    global _stream_task, _stream_running

    if not _stream_running:
        return {"status": "not_running", "message": "No stream is active."}

    _stream_running = False
    if _stream_task and not _stream_task.done():
        _stream_task.cancel()
        try:
            await _stream_task
        except asyncio.CancelledError:
            pass

    _stream_task = None
    return {"status": "stopped"}


@router.websocket("/stream/ws")
async def websocket_stream(websocket: WebSocket):
    """WebSocket endpoint for real-time transaction feed.

    Clients connect here to receive live transactions with ground truth
    labels and simulated ML risk scores.
    """
    await websocket.accept()
    _websocket_clients.add(websocket)
    logger.info("WebSocket client connected. Total clients: %d", len(_websocket_clients))

    try:
        while True:
            # Keep connection alive, receive any client messages (e.g., ping)
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    finally:
        _websocket_clients.discard(websocket)
        logger.info("WebSocket client disconnected. Total clients: %d", len(_websocket_clients))


# ── Background Stream Loop ──────────────────────────────────────────────────


async def _stream_loop(config: StreamConfig):
    """Background task that streams transactions to WebSocket clients."""
    global _stream_running

    if _cached_tx_df is None:
        logger.error("No cached dataset for streaming")
        _stream_running = False
        return

    delay = 1.0 / config.tps_rate
    tx_records = _cached_tx_df.to_dict("records")
    total = len(tx_records)

    logger.info("Starting stream: %d transactions at %d TPS", total, config.tps_rate)

    try:
        for i, tx in enumerate(tx_records):
            if not _stream_running:
                break

            # Compute simulated ML score
            ml_score = _compute_mock_ml_score(tx)

            payload = {
                "transaction_id": tx.get("transaction_id", f"TX_{i:08d}"),
                "tx_datetime": str(tx.get("tx_datetime", "")),
                "customer_id": tx.get("customer_id", ""),
                "terminal_id": tx.get("terminal_id", ""),
                "tx_amount": float(tx.get("tx_amount", 0)),
                "mcc": str(tx.get("mcc", "")),
                "payment_method": tx.get("payment_method", ""),
                "device_fingerprint": tx.get("device_fingerprint", ""),
                "ip_address": tx.get("ip_address", ""),
                "tx_fraud": int(tx.get("tx_fraud", 0)),
                "tx_fraud_scenario": int(tx.get("tx_fraud_scenario", 0)),
                "ml_risk_score": ml_score,
                "stream_index": i,
                "stream_total": total,
            }

            # Broadcast to all WebSocket clients
            message = json.dumps(payload, default=str)
            disconnected: set[WebSocket] = set()
            for ws in _websocket_clients:
                try:
                    await ws.send_text(message)
                except Exception:
                    disconnected.add(ws)

            _websocket_clients.difference_update(disconnected)

            await asyncio.sleep(delay)

    except asyncio.CancelledError:
        logger.info("Stream cancelled")
    except Exception as e:
        logger.error("Stream error: %s", e)
    finally:
        _stream_running = False
        logger.info("Stream ended after %d transactions", i + 1 if "i" in dir() else 0)
