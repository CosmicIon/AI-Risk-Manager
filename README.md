# 🛡️ AI Risk Manager: Enterprise BFSI Fraud Prevention & Risk Operations

[![CI](https://github.com/CosmicIon/AI-Risk-Manager/actions/workflows/ci.yml/badge.svg)](https://github.com/CosmicIon/AI-Risk-Manager/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.141+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-v2.1-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**AI Risk Manager** is a production-grade, defense-only fraud mitigation platform engineered for modern payment gateways, digital banking, and e-commerce checkouts. It bridges the gap between machine learning research and enterprise payments operations by providing **sub-50ms real-time API scoring**, **3-tier triage routing (Approve / OTP Challenge / Decline)**, **leakage-free walk-forward validation**, **automated Bayesian tuning**, and **continuous feature drift monitoring**.

---

## 🚀 Key Architectural Capabilities

```
                  ┌──────────────────────────────────────────────────────────┐
                  │                 Incoming Transaction                     │
                  └────────────────────────────┬─────────────────────────────┘
                                               │
                                               ▼
                         ┌───────────────────────────────────────────┐
                         │   FastAPI Real-Time Service (src/api.py)  │
                         │     - In-Memory Feature Store Cache       │
                         │     - Sub-15ms Spatial & Velocity Compute │
                         └─────────────────────┬─────────────────────┘
                                               │
                                               ▼
                         ┌───────────────────────────────────────────┐
                         │   LightGBM Classifier + SHAP Explainers   │
                         │     - Calibrated Risk Probability Score   │
                         └─────────────────────┬─────────────────────┘
                                               │
                                               ▼
                         ┌───────────────────────────────────────────┐
                         │       3-Tier Dynamic Action Policy        │
                         └───────┬─────────────┬─────────────┬───────┘
                                 │             │             │
                    p < 0.30     │ 0.30<=p<t*  │     p >= t* │
                                 ▼             ▼             ▼
                           🟢 APPROVE    🟡 CHALLENGE    🔴 DECLINE
                           (Friction-     (Step-Up SMS/  (Automated
                            Free Pay)      3DS Auth)      Hard Block)
```

### 1. 🟢 3-Tier Enterprise Risk Triage Policy
Replaces naive binary (Flag/Clear) decisions with risk-calibrated triage routing:
- **🟢 Tier 1: Approve ($p < 0.30$)** — Instant, zero-friction 1-click checkout for legitimate buyers.
- **🟡 Tier 2: Challenge ($0.30 \le p < t^*$)** — Step-up verification via SMS OTP or 3D-Secure. Legitimate users pass easily, while fraudsters holding stolen credentials fail.
- **🔴 Tier 3: Decline ($p \ge t^*$)** — Automated block or analyst review for high-probability threats.

### 2. ⚡ Real-Time FastAPI Scoring Microservice (`src/api.py`)
- **Sub-50ms SLA**: Delivers $<15\text{ms}$ median inference latency via an in-memory profile and rolling statistical cache (`InMemoryFeatureStore`).
- **Human-Readable Reason Codes**: Context-aware explanation engine translates multivariate anomalies into plain-English analyst notes (e.g. *"Transaction amount ($480.00) is 8.2x higher than 30-day baseline"*).
- **Observability**: Built-in `/health` readiness probes and `/metrics` telemetry tracking P95 latency and decision volume distributions.

### 3. 🛡️ Purged Walk-Forward Time-Series Cross-Validation (`src/cross_validate.py`)
- Standard K-fold cross-validation causes catastrophic lookahead leakage and inflates offline performance.
- Implements **expanding-window walk-forward validation** with a **7-day purged embargo buffer** between train and test windows, replicating real-world chargeback reporting delays and proving model stability over time.

### 4. 🧪 Automated Hyperparameter Optimization via Optuna (`src/tune.py`)
- Bayesian optimization using Tree-structured Parzen Estimators (TPE).
- Searches tree depth, leaf count, learning rates, subsampling ratios, and class-imbalance weight multipliers directly maximizing **PR-AUC (Precision-Recall Area Under Curve)** against out-of-time temporal validation slices.

### 5. 📈 Population Stability Index (PSI) & Drift Monitoring (`src/drift.py`)
- Computes **PSI** for all 21 engineered features between training baselines and production test data:
  - 🟢 **STABLE** ($\text{PSI} < 0.10$)
  - 🟡 **MODERATE_SHIFT** ($0.10 \le \text{PSI} \le 0.25$)
  - 🔴 **SIGNIFICANT_DRIFT** ($\text{PSI} > 0.25$ — Automated retraining trigger)
- Automatically monitors **Concept Drift** ($\Delta \text{Fraud Rate}\%$) and prediction score drift, exporting executive markdown reports to [`reports/drift_report.md`](reports/drift_report.md).

### 6. 🔌 Vectorized Simulation & Real-World Dataset Adapters (`src/adapters/`)
- Vectorized 2D Euclidean distance matrix computation accelerates customer-terminal proximity matching by $>50\times$.
- Plug-and-play schema adapters standardizing raw public benchmarks into the unified pipeline schema:
  - **Kaggle Credit Card Fraud** (`src/adapters/kaggle.py`)
  - **IEEE-CIS Fraud Detection Benchmark** (`src/adapters/ieee_cis.py`)

### 7. 🖥️ Interactive Risk Operations Dashboard (`src/dashboard.py`)
- Live 3-tier triage cards displaying real-time traffic distributions.
- **Dual-threshold simulator** recalculating Approve / Challenge / Decline volumes and losses dynamically.
- **Interactive Unit Economics Adjuster**: Real-time adjustment of False Alarm Cost, Chargeback Penalty, and OTP Challenge Fee recalculating net merchant savings live in the browser.

---

## 📊 Feature Engineering Specification (21 Features)

| Feature | Category | Description |
| :--- | :--- | :--- |
| `TX_AMOUNT` | Transaction | Monetary transaction amount in currency units |
| `TX_DURING_WEEKEND` | Temporal | Binary flag (1 if Saturday/Sunday, else 0) |
| `TX_DURING_NIGHT` | Temporal | Binary flag (1 if off-hours: 00:00 to 06:00, else 0) |
| `TX_DIST_CUSTOMER_TERMINAL` | Spatial | Euclidean distance between customer home anchor $(x, y)$ and terminal $(x, y)$ |
| `CUSTOMER_ID_NB_TX_15MIN_WINDOW` | Velocity | Sub-hour transaction burst count within preceding 15 minutes |
| `CUSTOMER_ID_NB_TX_1HOUR_WINDOW` | Velocity | Transaction count in preceding 1 hour |
| `TIME_SINCE_LAST_TX` | Velocity | Elapsed seconds since the customer's previous transaction |
| `CUSTOMER_ID_NB_TX_1DAY_WINDOW` | Profile | Customer transaction frequency over 1-day rolling window |
| `CUSTOMER_ID_AVG_AMOUNT_1DAY_WINDOW` | Profile | Customer average spend over 1-day rolling window |
| `CUSTOMER_ID_NB_TX_7DAY_WINDOW` | Profile | Customer transaction frequency over 7-day rolling window |
| `CUSTOMER_ID_AVG_AMOUNT_7DAY_WINDOW` | Profile | Customer average spend over 7-day rolling window |
| `CUSTOMER_ID_NB_TX_30DAY_WINDOW` | Profile | Customer transaction frequency over 30-day rolling window |
| `CUSTOMER_ID_AVG_AMOUNT_30DAY_WINDOW`| Profile | Customer 30-day baseline average spend |
| `CUSTOMER_ID_STD_AMOUNT_30DAY_WINDOW`| Profile | Customer-specific rolling 30-day standard deviation |
| `TX_AMOUNT_ZSCORE` | Anomaly | Per-customer standard deviation Z-score: $(x - \mu_{30\text{d}}) / (\sigma_{30\text{d}} + 1.0)$ |
| `TERMINAL_ID_NB_TX_1DAY_WINDOW` | Terminal | Terminal transaction count over 1-day rolling window |
| `TERMINAL_ID_RISK_1DAY_WINDOW` | Terminal | 7-day delay-purged historical fraud risk score for terminal (1-day) |
| `TERMINAL_ID_NB_TX_7DAY_WINDOW` | Terminal | Terminal transaction count over 7-day rolling window |
| `TERMINAL_ID_RISK_7DAY_WINDOW` | Terminal | 7-day delay-purged historical fraud risk score for terminal (7-day) |
| `TERMINAL_ID_NB_TX_30DAY_WINDOW` | Terminal | Terminal transaction count over 30-day rolling window |
| `TERMINAL_ID_RISK_30DAY_WINDOW` | Terminal | 7-day delay-purged historical fraud risk score for terminal (30-day) |

---

## 🛠️ Quickstart Guide

### 1. Environment Setup
```powershell
# Clone the repository
git clone https://github.com/CosmicIon/AI-Risk-Manager.git
cd AI-Risk-Manager

# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\activate

# Install all production & testing dependencies
pip install -r requirements.txt
```

### 2. Run the Modular End-to-End Pipeline
```powershell
# 1. Ingestion (Vectorized simulation or Kaggle/IEEE-CIS benchmark)
python -m src.ingestion --source simulator

# 2. Feature Engineering (Spatial distance, rolling variance, burst velocity)
python -m src.features

# 3. Train/Test Time-Series Split
python -m src.split

# 4. Model Training with Walk-Forward Purged Cross-Validation
python -m src.train --cv

# 5. Cost-Sensitive Multi-Threshold Evaluation & Triage Routing
python -m src.evaluate

# 6. SHAP Defense-Only Explainability Generation
python -m src.explain
```

### 3. Launch Real-Time Scoring API (FastAPI)
```powershell
uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
```
- Interactive OpenAPI / Swagger UI: **`http://localhost:8000/docs`**
- Health check: **`http://localhost:8000/health`**
- Operational telemetry: **`http://localhost:8000/metrics`**

#### Sample Real-Time Scoring Request:
```bash
curl -X POST "http://localhost:8000/v1/risk/evaluate" \
     -H "Content-Type: application/json" \
     -d '{
       "transaction_id": 9002,
       "customer_id": 1,
       "terminal_id": 99,
       "tx_amount": 4800.0,
       "tx_datetime": "2026-09-05T03:15:00"
     }'
```

#### Sample Response (<15ms Latency):
```json
{
  "transaction_id": 9002,
  "risk_score": 0.8942,
  "decision": "DECLINE",
  "latency_ms": 11.35,
  "reasons": [
    "Transaction amount ($4800.00) is 92.3x higher than 30-day baseline ($52.00).",
    "High spending deviation: Z-score is +218.18 standard deviations.",
    "Off-hours transaction initiated during high-risk night window (00:00 - 06:00)."
  ],
  "timestamp": "2026-09-05T01:30:00.123456Z"
}
```

### 4. Launch the Interactive Operations Dashboard
```powershell
streamlit run src/dashboard.py
```
Access the dashboard at **`http://localhost:8501`** to adjust dynamic unit economics, simulate dual-threshold triage policies, and review SHAP waterfall explainers.

### 5. Run Automated Hyperparameter Tuning (Optuna)
```powershell
python -m src.tune --n-trials 25 --update-config
```

### 6. Run Statistical Drift & PSI Monitoring
```powershell
python -m src.drift
```
Inspect the generated executive report at [`reports/drift_report.md`](reports/drift_report.md).

---

## 🧪 Comprehensive Quality Assurance & Testing

The project includes an enterprise test suite of **35 automated unit and integration tests** executing via `pytest`:

```powershell
pytest -v
```

### Test Suite Coverage:
- **`tests/test_api.py`** (7 tests): Validates endpoint contracts, sub-50ms latency SLAs, micro-batch scoring, and telemetry counters.
- **`tests/test_leakage.py`** (3 tests): Mathematically proves zero future lookahead leakage, strict 7-day reporting delay enforcement, and dataset isolation.
- **`tests/test_validation.py`** (5 tests): Verifies temporal ordering, embargo purging, and expanding window invariants in walk-forward CV.
- **`tests/test_tune.py`** (3 tests): Tests temporal split generation, objective function scoring, and Optuna parameter boundary compliance.
- **`tests/test_drift.py`** (5 tests): Tests PSI numerical accuracy, zero-shift stability, moderate shift sensitivity, and report generation.
- **`tests/test_adapters.py`** (4 tests): Tests 2D spatial broadcasting and Kaggle/IEEE-CIS schema normalization.
- **`tests/test_triage.py`** (3 tests): Tests 3-tier boundary conditions, partition completeness, and OTP revenue recovery logic.
- **`tests/test_features.py`** (4 tests): Tests per-customer Z-score variance, burst velocity, and distance anomalies.
- **`tests/test_pipeline_smoke.py`** (1 test): End-to-end integration smoke test.

Continuous Integration is automated via **GitHub Actions** ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) across Python 3.11 and 3.12.

---

## ⚖️ Defense-Only Compliance & Ethics Policy

**Strictly Defensive Scope:** This software is designed exclusively for authorized fraud detection, fraud risk assessment, and financial transaction security. It is built to assist fraud analysts and merchant operations teams. It contains no offensive adversarial generation, payload evasion tools, or code designed to circumvent anti-fraud controls. All explainability outputs are framed from the perspective of risk management and compliance transparency.

---

## 📄 License
This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
