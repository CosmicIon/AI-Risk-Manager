# 🎯 Solving the Problem Statement: AI Risk Manager & Feature Catalog

This document provides an in-depth breakdown of how the **AI Risk Manager** directly solves the hackathon problem statement defined in [`problem_statement.md`](file:///d:/CODING/github/AI-Risk-Manager/problem_statement.md), followed by an exhaustive catalog of all project features (both **System Capabilities** and **Engineered Machine Learning Features**).

---

## 📋 The Problem Statement at a Glance

From [`problem_statement.md`](file:///d:/CODING/github/AI-Risk-Manager/problem_statement.md):

> **Track 02: AI Risk Manager**  
> *Stop the merchant losing money to fraud, returns and chargebacks.*  
> 
> * **Deliverable:** Build a working detector, verifier, or auto-responder for one class of loss, with measured precision and recall on a held-out test set.  
> * **Why Now:** AI-enabled fraud is hitting Indian BFSI while returns and chargebacks quietly eat margin. This track surfaces the risk and ML-minded builders the others miss.  
> * **Constraints:** Honest metrics including false-positive cost. Strictly defense-only: anything offense-capable is disqualified.

---

## 🧩 Requirement-by-Requirement Solution Mapping

Here is how our project addresses every single requirement set forth by the track:

| Track Requirement | Problem Identified | How AI Risk Manager Solves It | Source Code Proof |
| :--- | :--- | :--- | :--- |
| **1. One Class of Loss** | Card-Not-Present (CNP) fraud and chargebacks eating merchant margins. | Detects unauthorized card use, hijacked accounts, credential stuffing, and compromised terminals across 180 simulated days (1.75M transactions). | [`src/ingestion.py`](file:///d:/CODING/github/AI-Risk-Manager/src/ingestion.py) |
| **2. Working Detector** | Batch ML models fail to run in real-time checkout gateways. | Ultra-fast LightGBM classifier with class imbalance weighting (`scale_pos_weight`) delivering predictions in microseconds. | [`src/train.py`](file:///d:/CODING/github/AI-Risk-Manager/src/train.py) |
| **3. Working Verifier & Auto-Responder** | Binary Flag/Clear either loses revenue or creates massive customer anger. | **3-Tier Action Policy**: 🟢 `APPROVE` (Frictionless), 🟡 `CHALLENGE` (Step-up SMS OTP / 3DS), 🔴 `DECLINE` (Hard block). Auto-responds via FastAPI in $<15\text{ms}$. | [`src/api.py`](file:///d:/CODING/github/AI-Risk-Manager/src/api.py), [`src/dashboard.py`](file:///d:/CODING/github/AI-Risk-Manager/src/dashboard.py) |
| **4. Measured Precision & Recall on Held-out Test Set** | High accuracy scores are deceptive on imbalanced fraud datasets (<1% fraud). | Evaluates **PR-AUC** and **Precision-Recall curves** on 54 days of out-of-time held-out data (Days 127–180). | [`src/evaluate.py`](file:///d:/CODING/github/AI-Risk-Manager/src/evaluate.py) |
| **5. Honest Metrics (False-Positive Cost)** | Most models pick arbitrary 0.5 thresholds, ignoring real dollar friction. | Sweeps 99 thresholds to minimize: $\text{Cost} = \text{FP} \times \$5.00 + \text{FN} \times \$128.44$. Achieves **74% net financial loss reduction** ($491,816 saved). | [`src/evaluate.py`](file:///d:/CODING/github/AI-Risk-Manager/src/evaluate.py), [`models/metrics_test.json`](file:///d:/CODING/github/AI-Risk-Manager/models/metrics_test.json) |
| **6. Why Now (Indian BFSI Realities)** | Fraudsters use automated script bursts; Indian regulations mandate 2FA/OTP. | Sub-hour 15-minute velocity counters catch script attacks; 3-tier OTP step-up verification mimics RBI/3DS workflows. | [`src/features.py`](file:///d:/CODING/github/AI-Risk-Manager/src/features.py), [`src/api.py`](file:///d:/CODING/github/AI-Risk-Manager/src/api.py) |
| **7. Strictly Defense-Only** | Adversarial generators or evasion tools pose dangerous misuse risks. | 100% defense-oriented. SHAP explanations translate into plain English strictly for fraud analysts. Zero adversarial evasion tools. | [`src/explain.py`](file:///d:/CODING/github/AI-Risk-Manager/src/explain.py) |

---

## 🚀 Part 1: Platform & System Features

The project is not just a Jupyter notebook model; it is an enterprise-grade software platform consisting of **10 major architectural capabilities**:

```mermaid
flowchart TD
    subgraph Ingestion_Layer ["1. Ingestion & Adapters"]
        SIM["Vectorized Ingestion Simulator"]
        ADAPT["Kaggle & IEEE-CIS Adapters"]
    end

    subgraph Feature_Layer ["2. Feature Engine"]
        FEAT["21 Leakage-Free Features<br/>(Velocity, Spatial, Profiles)"]
        DELAY["7-Day Lagged Terminal Risk"]
    end

    subgraph Modeling_Layer ["3. ML & Validation"]
        SPLIT["7-Day Embargo Temporal Split"]
        WF["Walk-Forward 3-Fold CV"]
        OPT["Optuna Bayesian Tuning"]
        LGB["Class-Weighted LightGBM"]
    end

    subgraph Operations_Layer ["4. Production Operations"]
        API["FastAPI Real-Time Service (<15ms)"]
        TRIAGE["3-Tier Triage Policy<br/>(Approve / OTP / Decline)"]
        DASH["Streamlit Executive Cockpit"]
        DRIFT["PSI & Drift Monitoring"]
        TESTS["35 Automated CI Tests"]
    end

    SIM --> FEAT
    ADAPT --> FEAT
    FEAT --> SPLIT --> WF --> OPT --> LGB
    LGB --> API & DASH & DRIFT
    API --> TRIAGE
```

### 1. ⚡ Real-Time FastAPI Scoring Microservice (`src/api.py`)
- **Sub-50ms SLA Guarantee:** Delivers $<15\text{ms}$ median inference latency using an `InMemoryFeatureStore` cache.
- **REST Endpoints:**
  - `POST /v1/risk/evaluate`: Real-time transaction scoring with immediate 3-tier verdict and human reason codes.
  - `POST /v1/risk/evaluate/batch`: Micro-batch scoring for payment gateways (up to 100 transactions/request).
  - `GET /health`: Kubernetes-ready liveness probe checking model and feature store memory.
  - `GET /metrics`: Prometheus-compatible telemetry monitoring P95 latency and decision distribution counters.

### 2. 🟢 3-Tier Enterprise Risk Triage Policy
Replaces destructive binary "auto-decline" rules with modern fintech triage:
- **🟢 Tier 1: APPROVE ($p < 0.30$)** — Instant, frictionless 1-click checkout for trusted cardholders.
- **🟡 Tier 2: CHALLENGE ($0.30 \le p < t^*$)** — Triggers an instant SMS/WhatsApp OTP or 3D-Secure step-up prompt. Genuine cardholders authenticate in 5 seconds; criminals with stolen card details cannot supply the OTP, saving merchant revenue without churning legitimate users.
- **🔴 Tier 3: DECLINE ($p \ge t^*$)** — Immediate hard stop or high-priority manual analyst queue for critical threats.

### 3. 🛡️ Leakage-Free Temporal Split & 7-Day Embargo Buffer (`src/split.py`)
- Standard random train/test splits corrupt time-series models by training on future transactions to predict past events.
- We enforce strict chronological partitioning (Train: Days 30–120; Test: Days 127–180).
- An explicit **7-day embargo cooling buffer** (Days 121–126) is discarded completely so unresolved chargebacks cannot leak across the split boundary.

### 4. 📈 Purged Walk-Forward Time-Series Cross-Validation (`src/cross_validate.py`)
- Validates model generalization using a 3-fold expanding walk-forward split.
- Proves model stability over multiple quarters rather than a single lucky month.
- Emits cross-validation metrics with confidence intervals ($\mu \pm \sigma$).

### 5. 🧪 Bayesian Hyperparameter Optimization via Optuna (`src/tune.py`)
- Eliminates manual guesswork by searching tree depth, leaves, learning rates, subsampling ratios, and class imbalance weights using Tree-structured Parzen Estimators (TPE).
- Specifically optimizes for **PR-AUC** on out-of-time temporal validation folds.

### 6. 💰 Cost-Sensitive Threshold Sweep (`src/evaluate.py`)
- Replaces arbitrary 0.5 cutoffs with an empirical business cost equation:
  $$\text{Total Cost} = \text{False Positives} \times \$5.00 + \text{False Negatives} \times \$128.44$$
- Locates the mathematical cost minimum at **$t^* = 0.78$**, cutting net fraud losses by **74%**.

### 7. 🗣️ Plain-English Defense-Only Explainability Engine (`src/explain.py`)
- Uses tree-based SHAP (SHapley Additive exPlanations) to compute exact feature attributions.
- A linguistic translation engine converts mathematical log-odds into human analyst sentences (e.g. *"Transaction amount ($420.00) is 6.5x higher than customer's 30-day baseline"*).
- Strictly defense-only: no evasion guidance or adversarial hints.

### 8. 🖥️ Interactive Risk Operations Dashboard (`src/dashboard.py`)
- Built with Streamlit for risk managers and C-level fraud executives:
  - **Verdict Banner**: Instant executive summary of system performance.
  - **Live 60 FPS Dual-Threshold Simulator**: Sliders to test Approve/Challenge/Decline cutoffs and see financial impact in real time.
  - **Dynamic Unit Economics Adjuster**: Modify False Alarm Cost ($5 to $25) or Chargeback Penalty ($50 to $300) live in the browser.
  - **Real-Time Flagged Transaction Feed**: Expandable cards with interactive SHAP waterfall plots and plain-English reasons.

### 9. 📉 Population Stability Index (PSI) & Concept Drift Monitoring (`src/drift.py`)
- Continuously assesses whether customer spending behavior or fraud tactics have changed between training baselines and live production traffic.
- Computes PSI for all 21 features with automated severity tags:
  - 🟢 **STABLE** ($\text{PSI} < 0.10$)
  - 🟡 **MODERATE_SHIFT** ($0.10 \le \text{PSI} \le 0.25$)
  - 🔴 **SIGNIFICANT_DRIFT** ($\text{PSI} > 0.25$ — Retraining Alert)
- Generates markdown audits in [`reports/drift_report.md`](file:///d:/CODING/github/AI-Risk-Manager/reports/drift_report.md).

### 10. 🔌 Real-World Dataset Adapters (`src/adapters/`)
- Demonstrates dataset-agnostic architecture through plug-and-play schema adapters:
  - **Kaggle Credit Card Fraud** (`src/adapters/kaggle.py`)
  - **IEEE-CIS Fraud Detection Benchmark** (`src/adapters/ieee_cis.py`)

---

## 🔬 Part 2: The 21 Engineered Machine Learning Features

Fraudsters cannot hide their physical and behavioral anomalies when features are engineered across multiple time horizons and spatial dimensions. 

Here is the complete catalog of **all 21 features** engineered in [`src/features.py`](file:///d:/CODING/github/AI-Risk-Manager/src/features.py):

| # | Feature Name | Category | Exact Mathematical Formulation / Logic | What Pattern It Catches |
| :---: | :--- | :--- | :--- | :--- |
| **1** | `TX_AMOUNT` | Monetary | Raw monetary transaction value ($) | High-ticket theft and card balance draining. |
| **2** | `TX_DURING_WEEKEND` | Temporal | $1 \text{ if Day of Week} \in \{\text{Sat, Sun}\} \text{ else } 0$ | Weekend shopping anomalies when customer service centers are closed. |
| **3** | `TX_DURING_NIGHT` | Temporal | $1 \text{ if Hour} \in [0, 6) \text{ else } 0$ | High-risk overnight unauthorized transactions (2:00 AM – 5:00 AM). |
| **4** | `TX_DIST_CUSTOMER_TERMINAL` | Spatial | $\sqrt{(x_{\text{cust}} - x_{\text{term}})^2 + (y_{\text{cust}} - y_{\text{term}})^2}$ | Card cloning and remote skimming where card is tapped far from customer home. |
| **5** | `CUSTOMER_ID_NB_TX_15MIN_WINDOW` | Velocity | $\sum \text{Transactions in past 15 minutes}$ | High-frequency bot testing and credential stuffing scripts. |
| **6** | `CUSTOMER_ID_NB_TX_1HOUR_WINDOW` | Velocity | $\sum \text{Transactions in past 60 minutes}$ | Rapid balance draining before customer can call the bank. |
| **7** | `TIME_SINCE_LAST_TX` | Velocity | $\Delta t = t_i - t_{i-1} \text{ (seconds)}$ | Detects impossible physical travel (e.g. 2 swipes 100 miles apart in 2 minutes). |
| **8** | `CUSTOMER_ID_NB_TX_1DAY_WINDOW` | Profile | Rolling 1-day transaction count for customer | Sudden spike in daily swipe frequency. |
| **9** | `CUSTOMER_ID_AVG_AMOUNT_1DAY_WINDOW` | Profile | Rolling 1-day mean transaction spend for customer | Short-term spending spree behavior. |
| **10** | `CUSTOMER_ID_NB_TX_7DAY_WINDOW` | Profile | Rolling 7-day transaction count for customer | Weekly frequency baseline. |
| **11** | `CUSTOMER_ID_AVG_AMOUNT_7DAY_WINDOW` | Profile | Rolling 7-day mean transaction spend for customer | Weekly spend baseline. |
| **12** | `CUSTOMER_ID_NB_TX_30DAY_WINDOW` | Profile | Rolling 30-day transaction count for customer | Monthly customer loyalty and engagement tier. |
| **13** | `CUSTOMER_ID_AVG_AMOUNT_30DAY_WINDOW` | Profile | $\mu_{30\text{d}} = \text{Rolling 30-day mean spend}$ | Long-term personal monetary baseline. |
| **14** | `CUSTOMER_ID_STD_AMOUNT_30DAY_WINDOW` | Profile | $\sigma_{30\text{d}} = \text{Customer-specific 30-day standard dev}$ | Measures customer's individual spending variance. |
| **15** | `TX_AMOUNT_ZSCORE` | Anomaly | $Z = \frac{\text{Amount} - \mu_{30\text{d}}}{\sigma_{30\text{d}} + 1.0}$ | Normalized individual spend anomaly (flags $100 swipe for a $10 spender). |
| **16** | `TERMINAL_ID_NB_TX_1DAY_WINDOW` | Terminal | Terminal transaction count over 1-day window | Abnormal merchant terminal volume surges. |
| **17** | `TERMINAL_ID_RISK_1DAY_WINDOW` | Terminal Risk | 7-day lagged fraud rate for terminal over 1 day | Compromised terminal detection (leakage-free). |
| **18** | `TERMINAL_ID_NB_TX_7DAY_WINDOW` | Terminal | Terminal transaction count over 7-day window | Weekly terminal activity level. |
| **19** | `TERMINAL_ID_RISK_7DAY_WINDOW` | Terminal Risk | 7-day lagged fraud rate for terminal over 7 days | Sustained compromised merchant compromise. |
| **20** | `TERMINAL_ID_NB_TX_30DAY_WINDOW` | Terminal | Terminal transaction count over 30-day window | Monthly terminal throughput baseline. |
| **21** | `TERMINAL_ID_RISK_30DAY_WINDOW` | Terminal Risk | 7-day lagged fraud rate for terminal over 30 days | Long-term rogue terminal indicator. |

---

## 💰 Business Impact & Financial ROI

When presenting to judges or financial officers, these are the real numbers from our held-out test evaluation:

| Metric | Without AI Risk Manager (Flag Nothing) | Naive Industry Model (Flag Everything) | **With AI Risk Manager ($t^*=0.78$)** |
| :--- | :---: | :---: | :---: |
| **Fraud Losses** | $664,972.49 | $0.00 | **$124,000.00** |
| **Operational Review Costs** | $0.00 | $5,253,320.00 | **$49,156.38** |
| **Total Net Cost** | $664,972.49 | $5,253,320.00 | **$173,156.38** |
| **Net Money Saved** | $0.00 | -$4,588,347.51 | **+$491,816.11** |
| **Cost Reduction %** | 0.0% | Catastrophic Loss | **74.0% Reduction** |
| **Legitimate Orders Cleared** | 100% | 0% (Total business shutdown) | **99.4% Cleared Seamlessly** |

---

## ⚖️ Defense-Only Compliance Commitment

In accordance with the track mandate:
1. **Zero Evasion Utility:** The system produces risk scores, anomaly reason codes, and triage routing. It contains no tools to bypass 2FA, generate spoofed cards, reverse-engineer biometric defenses, or manipulate risk scores.
2. **Defensive Explainability:** All SHAP and linguistic outputs are explicitly formulated for compliance officers, fraud investigators, and consumer protection teams.
3. **Audit Ready:** Every decision made by the FastAPI service records timestamp, latency, decision rationale, and model version for regulatory transparency.
