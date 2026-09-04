# AI Risk Manager: Engineering Improvement Plan & TODO Checklist

This document details all planned fixes, architectural upgrades, and optimizations organized **module-by-module**. Implementing these items will transition the project from a research/demonstration prototype into an industry-grade, production-ready BFSI fraud mitigation system.

---

## 📋 Quick Roadmap Summary

| Module | Priority | Focus Area | Status |
| :--- | :---: | :--- | :---: |
| **Module 3: Features** (`src/features.py`) | **HIGH** | Fix global std Z-score bug, add distance & burst velocity features | `[x] Completed` |
| **Module 8: Dashboard** (`src/dashboard.py`) | **HIGH** | Upgrade to 3-tier triage policy (Approve / OTP / Decline) | `[x] Completed` |
| **Module 6: Evaluation** (`src/evaluate.py`) | **HIGH** | Multi-threshold cost matrix & friction-loss balance | `[x] Completed` |
| **Module 5: Model Training** (`src/train.py`) | **MEDIUM** | Walk-forward rolling time-series cross-validation | `[ ] Pending` |
| **Module 9: API Serving** (`src/api.py`) | **MEDIUM** | Real-time FastAPI sub-50ms inference endpoint | `[ ] Pending` |
| **Module 10: Model Monitoring** (`src/drift.py`) | **MEDIUM** | Population Stability Index (PSI) & feature drift detection | `[ ] Pending` |
| **Module 1: Ingestion** (`src/ingestion.py`) | **LOW** | Vectorization optimization & real-world dataset adapter | `[ ] Pending` |
| **Module 11: CI/CD & Testing** (`tests/`, `.github/`) | **LOW** | Feature leakage unit tests & automated GitHub Actions CI | `[ ] Pending` |

---

## 1. Feature Engineering Module (`src/features.py`)

### 1.1 Fix Per-Customer Standard Deviation in Spending Z-Score
* **Priority:** 🔴 **HIGH** (Bug / Statistical Flaw)
* **Status:** `[x] Completed`
* **Current Issue:**
  In `src/features.py` (Line 121), `TX_AMOUNT_ZSCORE` computes:
  ```python
  transactions['TX_AMOUNT_ZSCORE'] = (
      transactions['TX_AMOUNT'] - transactions['CUSTOMER_ID_AVG_AMOUNT_30DAY_WINDOW']
  ) / (transactions.rolling('30d', on='TX_DATETIME')['TX_AMOUNT'].std().fillna(1.0) + 0.001)
  ```
  The denominator calculates the standard deviation over the **entire global dataset across all 10,000 customers**, rather than the specific customer's spending variance. A customer with a steady $10 spend history will have their variance measured against high-spenders ($500+).
* **Fix Implementation:**
  Compute rolling standard deviation directly inside `get_customer_spending_behaviours_features`:
  ```python
  # Calculate 30-day customer-specific standard deviation
  customer_transactions['CUSTOMER_ID_STD_AMOUNT_30DAY_WINDOW'] = (
      customer_transactions.rolling('30D', on='TX_DATETIME')['TX_AMOUNT'].std().fillna(0.0)
  )
  
  # Customer-specific Z-Score
  customer_transactions['TX_AMOUNT_ZSCORE'] = (
      customer_transactions['TX_AMOUNT'] - customer_transactions['CUSTOMER_ID_AVG_AMOUNT_30DAY_WINDOW']
  ) / (customer_transactions['CUSTOMER_ID_STD_AMOUNT_30DAY_WINDOW'] + 1.0)
  ```
* **Impact:** Drastically reduces false alarms for legitimate users with naturally variable spending, while sharpening anomaly detection for consistent low-spenders.

---

### 1.2 Customer-Terminal Spatial Distance Feature
* **Priority:** 🔴 **HIGH**
* **Status:** `[x] Completed`
* **Current Issue:**
  Customer profiles (`customer_profiles.pkl`) and terminal profiles (`terminal_profiles.pkl`) contain 2D coordinates `(x, y)` on a 100x100 grid. Currently, `features.py` ignores these coordinates after ingestion.
* **Fix Implementation:**
  Merge coordinates and compute the Euclidean distance for every transaction:
  $$\text{DIST\_CUSTOMER\_TERMINAL} = \sqrt{(x_{\text{cust}} - x_{\text{term}})^2 + (y_{\text{cust}} - y_{\text{term}})^2}$$
  Also compute the customer's average historical radius:
  $$\text{DIST\_ANOMALY\_RATIO} = \frac{\text{DIST\_CUSTOMER\_TERMINAL}}{\text{AVG\_DIST\_30DAY} + \epsilon}$$
* **Impact:** Instantly flags card-cloning and remote skimming attacks where stolen credentials are used far away from the customer's geographic anchor.

---

### 1.3 Sub-Hour Transaction Burst & Velocity Features
* **Priority:** 🔴 **HIGH**
* **Status:** `[x] Completed`
* **Current Issue:**
  Rolling windows are only computed at coarse intervals: 1-day, 7-day, and 30-day. Fraudsters frequently "card test" with micro-transactions or drain balances within minutes.
* **Fix Implementation:**
  Add high-resolution rolling windows for customer and terminal:
  - `CUSTOMER_NB_TX_15MIN_WINDOW`: Transaction count in preceding 15 minutes.
  - `CUSTOMER_NB_TX_1HOUR_WINDOW`: Transaction count in preceding 1 hour.
  - `TIME_SINCE_LAST_TX`: Elapsed time in seconds since the customer's previous transaction:
    ```python
    customer_transactions['TIME_SINCE_LAST_TX'] = (
        customer_transactions['TX_DATETIME'].diff().dt.total_seconds().fillna(86400)
    )
    ```
* **Impact:** Provides a strong predictive signal for automated script-based card draining and credential stuffing attacks.

---

## 2. Decision Logic & Dashboard Module (`src/dashboard.py` & `src/evaluate.py`)

### 2.1 Transition to a 3-Tier Action Policy (Approve / Challenge / Decline)
* **Priority:** 🔴 **HIGH**
* **Status:** `[x] Completed`
* **Current Issue:**
  The system currently makes a binary choice: Flag or Clear. In enterprise fraud operations, auto-declining transactions creates severe customer drop-off.
* **Fix Implementation:**
  Implement a dynamic 3-tier risk triage:
  1. **Low Risk ($p < 0.30$):** `APPROVE` — Instant, friction-free checkout.
  2. **Medium Risk ($0.30 \le p < 0.78$):** `CHALLENGE (OTP / 3DS)` — Customer completes step-up SMS/app verification. If legitimate, transaction clears; if fraudulent, fraudster cannot supply OTP.
  3. **High Risk ($p \ge 0.78$):** `DECLINE / MANUAL REVIEW` — Hard block or analyst queue.
* **Dashboard Enhancements:**
  - Added a dedicated 3-way triage card strip on the UI showing the distribution of Approved vs. Challenged vs. Declined orders.
  - Added dynamic dual-slider simulator recalculating 3-tier distribution in real time.

---

### 2.2 Dynamic Operational Cost Adjuster on Dashboard
* **Priority:** 🟡 **MEDIUM**
* **Status:** `[x] Completed`
* **Current Issue:**
  False positive cost ($5.00) and false negative cost ($128.44) are hardcoded. Different merchant categories (e.g., electronics vs. digital gaming) have vastly different unit economics.
* **Fix Implementation:**
  Added interactive sidebar inputs in `src/dashboard.py`:
  - `Cost per False Alarm Review ($)`
  - `Cost per Missed Fraud / Chargeback ($)`
  - `Cost per OTP / SMS Challenge ($)`
  - Dynamically recalculates net savings, efficiency multiplier, and confusion matrix dollar figures live in the browser.

---

## 3. Model Training & Validation Module (`src/train.py` & `src/split.py`)

### 3.1 Walk-Forward Purged Time-Series Cross-Validation
* **Priority:** 🟡 **MEDIUM**
* **Status:** `[ ] Pending`
* **Current Issue:**
  The model is currently validated on a single static split (Train: Days 30–120; Test: Days 127–180). This leaves the model vulnerable to variance from a single lucky/unlucky time window.
* **Fix Implementation:**
  Implement a 3-fold Walk-Forward Cross-Validation with a 7-day embargo buffer between folds:
  - **Fold 1:** Train [Day 30–75] $\rightarrow$ Embargo [75–82] $\rightarrow$ Test [82–105]
  - **Fold 2:** Train [Day 30–110] $\rightarrow$ Embargo [110–117] $\rightarrow$ Test [117–140]
  - **Fold 3:** Train [Day 30–145] $\rightarrow$ Embargo [145–152] $\rightarrow$ Test [152–180]
  Report mean PR-AUC and standard deviation: $\mu_{\text{PR-AUC}} \pm \sigma$.
* **Impact:** Proves temporal stability and validates that hyperparameter settings do not overfit a specific month.

---

### 3.2 Automated Hyperparameter Optimization (Optuna)
* **Priority:** 🟡 **MEDIUM**
* **Status:** `[ ] Pending`
* **Current Issue:**
  LightGBM tree hyperparameters (`num_leaves: 31`, `learning_rate: 0.05`, `max_depth: 6`) are static in `config.yaml`.
* **Fix Implementation:**
  Add `src/tune.py` utilizing Optuna to search:
  - `num_leaves`: [15, 63]
  - `min_child_samples`: [20, 100]
  - `subsample` & `colsample_bytree`: [0.6, 0.95]
  - `scale_pos_weight` multiplier bounds.
  Objective function: Maximize PR-AUC on the validation slice.

---

## 4. Real-Time Production Serving Module (`src/api.py`)

### 4.1 FastAPI Real-Time Scoring Microservice
* **Priority:** 🟡 **MEDIUM**
* **Status:** `[ ] Pending`
* **Current Issue:**
  The system currently only scores batch parquet files. Checkout gateways require synchronous JSON API scoring with $<50\text{ms}$ latency.
* **Fix Implementation:**
  Create `src/api.py` with FastAPI:
  - **Endpoint:** `POST /v1/risk/evaluate`
  - **Payload:**
    ```json
    {
      "transaction_id": 1058291,
      "customer_id": 4821,
      "terminal_id": 12049,
      "tx_amount": 340.50,
      "tx_datetime": "2026-09-04T14:32:00"
    }
    ```
  - **Response:**
    ```json
    {
      "risk_score": 0.842,
      "decision": "DECLINE",
      "latency_ms": 12.4,
      "reasons": [
        "Transaction amount is 4.8x higher than 30-day baseline",
        "Terminal risk score is elevated in past 7 days"
      ]
    }
    ```
  - Add `/health` and `/metrics` Prometheus-compatible endpoints.

---

## 5. Model Drift & Production Monitoring Module (`src/drift.py`)

### 5.1 Population Stability Index (PSI) & Concept Drift Detector
* **Priority:** 🟡 **MEDIUM**
* **Status:** `[ ] Pending`
* **Current Issue:**
  No automated detection of feature shift or changing fraud tactics across time.
* **Fix Implementation:**
  Build `src/drift.py`:
  - Calculate **PSI (Population Stability Index)** for every numerical feature between Training (Month 2–4) and Production Test (Month 5–6):
    $$\text{PSI} = \sum \left( \text{Actual}\% - \text{Expected}\% \right) \times \ln\left(\frac{\text{Actual}\%}{\text{Expected}\%}\right)$$
  - Flag alerts when $\text{PSI} > 0.25$ (Action required: Model retraining recommended).
  - Export a clean report: `reports/drift_report.md`.

---

## 6. Data Ingestion & Scalability Module (`src/ingestion.py`)

### 6.1 Polars / Vectorized Data Simulation
* **Priority:** 🟢 **LOW**
* **Status:** `[ ] Pending`
* **Current Issue:**
  Simulating 1.75M transactions uses sequential `pandas.apply` across 10,000 customer profiles, taking 4–6 minutes on standard hardware.
* **Fix Implementation:**
  Vectorize transaction generation with NumPy arrays or migrate ingestion and rolling windows to **Polars** for multithreaded processing in $<30$ seconds.

### 6.2 Real-World Dataset Adapter (IEEE-CIS / Kaggle Credit Card)
* **Priority:** 🟢 **LOW**
* **Status:** `[ ] Pending`
* **Current Issue:**
  Pipeline runs solely on synthetic simulated data.
* **Fix Implementation:**
  Add `src/adapters/ieee_cis.py` or `src/adapters/kaggle.py` allowing users to swap the data source from synthetic generation to the public IEEE-CIS Fraud Detection benchmark with a single config flag (`data_source: "ieee_cis"`).

---

## 7. Quality Assurance & CI/CD Pipeline (`tests/`, `.github/`)

### 7.1 Unit Tests for Feature Leakage
* **Priority:** 🟢 **LOW**
* **Status:** `[ ] Pending`
* **Current Issue:**
  Current smoke test only checks process exit codes (`0`) and artifact existence.
* **Fix Implementation:**
  Add `tests/test_leakage.py`:
  - Verify that terminal risk calculated at day $T$ strictly matches labels from $\le T - 7$.
  - Assert that no future timestamps appear in rolling window slices.
  - Assert that train and test indices have zero overlap.

### 7.2 GitHub Actions Automated CI Workflow
* **Priority:** 🟢 **LOW**
* **Status:** `[ ] Pending`
* **Fix Implementation:**
  Create `.github/workflows/ci.yml`:
  - Installs dependencies on `ubuntu-latest`.
  - Runs code linter (`flake8` / `ruff`).
  - Executes `pytest tests/test_pipeline_smoke.py`.
