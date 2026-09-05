# 🛡️ Production Model Drift & Stability Report

**Generated:** `2026-09-05T13:09:39.823690Z`  
**System Status:** 🟢 **HEALTHY** (Distributions Stable)  
**Recommendation:** All features are stable (PSI < 0.10). Model remains robust for production inference.

---

## 📊 Executive Monitoring Overview

| Metric | Training Baseline | Production Test | Delta / PSI | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Sample Volume** | 183,464 tx | 107,303 tx | - | - |
| **Fraud Prevalence** | 4.07% | 4.16% | +0.09% | `STABLE` |
| **Prediction Score Drift** | Baseline Scores | Production Scores | PSI = 0.0002 | `STABLE` |

---

## 🔍 Feature-Level Population Stability Index (PSI)

> **PSI Reference Thresholds:**  
> - $\text{PSI} < 0.10$: 🟢 **STABLE** (Minimal distribution change)  
> - $0.10 \le \text{PSI} \le 0.25$: 🟡 **MODERATE_SHIFT** (Monitor trends)  
> - $\text{PSI} > 0.25$: 🔴 **SIGNIFICANT_DRIFT** (Action required: Model retraining recommended)  

| Feature | PSI Score | Status | Train Mean ± Std | Test Mean ± Std |
| :--- | :---: | :---: | :---: | :---: |
| `CUSTOMER_ID_STD_AMOUNT_30DAY_WINDOW` | **0.0057** | 🟢 STABLE | 31.25 ± 32.26 | 31.27 ± 33.39 |
| `TERMINAL_ID_NB_TX_30DAY_WINDOW` | **0.0048** | 🟢 STABLE | 34.35 ± 12.14 | 34.94 ± 12.12 |
| `CUSTOMER_ID_NB_TX_30DAY_WINDOW` | **0.0047** | 🟢 STABLE | 80.61 ± 29.13 | 81.04 ± 29.26 |
| `CUSTOMER_ID_AVG_AMOUNT_30DAY_WINDOW` | **0.0036** | 🟢 STABLE | 55.69 ± 33.08 | 55.92 ± 32.97 |
| `TERMINAL_ID_RISK_30DAY_WINDOW` | **0.0018** | 🟢 STABLE | 0.04 ± 0.13 | 0.04 ± 0.13 |
| `CUSTOMER_ID_AVG_AMOUNT_7DAY_WINDOW` | **0.0015** | 🟢 STABLE | 55.72 ± 36.18 | 55.93 ± 36.46 |
| `CUSTOMER_ID_NB_TX_7DAY_WINDOW` | **0.0013** | 🟢 STABLE | 19.59 ± 7.74 | 19.67 ± 7.82 |
| `TERMINAL_ID_NB_TX_7DAY_WINDOW` | **0.0006** | 🟢 STABLE | 8.89 ± 3.76 | 8.92 ± 3.74 |
| `TX_AMOUNT` | **0.0002** | 🟢 STABLE | 55.64 ± 55.35 | 55.93 ± 56.68 |
| `TX_DIST_CUSTOMER_TERMINAL` | **0.0002** | 🟢 STABLE | 3.07 ± 1.42 | 3.07 ± 1.42 |
| `CUSTOMER_ID_AVG_AMOUNT_1DAY_WINDOW` | **0.0002** | 🟢 STABLE | 55.69 ± 43.69 | 55.83 ± 43.35 |
| `TERMINAL_ID_NB_TX_1DAY_WINDOW` | **0.0002** | 🟢 STABLE | 2.13 ± 1.12 | 2.14 ± 1.13 |
| `TIME_SINCE_LAST_TX` | **0.0001** | 🟢 STABLE | 42568.26 ± 86299.18 | 42522.82 ± 93877.88 |
| `CUSTOMER_ID_NB_TX_1DAY_WINDOW` | **0.0001** | 🟢 STABLE | 3.65 ± 1.87 | 3.66 ± 1.88 |
| `TX_AMOUNT_ZSCORE` | **0.0001** | 🟢 STABLE | 0.01 ± 0.97 | 0.01 ± 0.97 |
| `TERMINAL_ID_RISK_7DAY_WINDOW` | **0.0001** | 🟢 STABLE | 0.04 ± 0.16 | 0.04 ± 0.16 |
| `TX_DURING_WEEKEND` | **0.0000** | 🟢 STABLE | 0.28 ± 0.45 | 0.26 ± 0.44 |
| `TX_DURING_NIGHT` | **0.0000** | 🟢 STABLE | 0.13 ± 0.34 | 0.13 ± 0.34 |
| `CUSTOMER_ID_NB_TX_15MIN_WINDOW` | **0.0000** | 🟢 STABLE | 1.04 ± 0.19 | 1.04 ± 0.19 |
| `CUSTOMER_ID_NB_TX_1HOUR_WINDOW` | **0.0000** | 🟢 STABLE | 1.14 ± 0.38 | 1.14 ± 0.38 |
| `TERMINAL_ID_RISK_1DAY_WINDOW` | **0.0000** | 🟢 STABLE | 0.04 ± 0.18 | 0.04 ± 0.19 |

---

## 🛠️ Automated Retraining Policy
1. **Trigger Condition:** If $\ge 2$ core features exceed $\text{PSI} > 0.25$ OR prediction score $\text{PSI} > 0.25$, initiate automated walk-forward retraining (`python -m src.train --cv`).
2. **Data Pipeline Action:** If terminal risk or distance metrics drift, verify upstream geolocation lookups and feature windowing latency.
