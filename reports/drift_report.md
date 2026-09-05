# 🛡️ Production Model Drift & Stability Report

**Generated:** `2026-09-04T14:52:24.060764Z`  
**System Status:** 🔴 **ACTION REQUIRED** (Significant Drift Detected)  
**Recommendation:** Retraining recommended: 1 feature(s) show significant drift (PSI > 0.25). Review data sources and schedule model update.

---

## 📊 Executive Monitoring Overview

| Metric | Training Baseline | Production Test | Delta / PSI | Status |
| :--- | :---: | :---: | :---: | :---: |
| **Sample Volume** | 1,578 tx | 986 tx | - | - |
| **Fraud Prevalence** | 59.51% | 54.97% | -4.54% | `STABLE` |
| **Prediction Score Drift** | Baseline Scores | Production Scores | PSI = 0.5875 | `SIGNIFICANT_DRIFT` |

---

## 🔍 Feature-Level Population Stability Index (PSI)

> **PSI Reference Thresholds:**  
> - $\text{PSI} < 0.10$: 🟢 **STABLE** (Minimal distribution change)  
> - $0.10 \le \text{PSI} \le 0.25$: 🟡 **MODERATE_SHIFT** (Monitor trends)  
> - $\text{PSI} > 0.25$: 🔴 **SIGNIFICANT_DRIFT** (Action required: Model retraining recommended)  

| Feature | PSI Score | Status | Train Mean ± Std | Test Mean ± Std |
| :--- | :---: | :---: | :---: | :---: |
| `TERMINAL_ID_RISK_30DAY_WINDOW` | **0.2966** | 🔴 DRIFT ALERT | 0.42 ± 0.30 | 0.57 ± 0.32 |
| `CUSTOMER_ID_STD_AMOUNT_30DAY_WINDOW` | **0.2450** | 🟡 MODERATE | 235.11 ± 351.82 | 256.91 ± 334.58 |
| `CUSTOMER_ID_AVG_AMOUNT_30DAY_WINDOW` | **0.2331** | 🟡 MODERATE | 139.84 ± 142.43 | 152.19 ± 148.31 |
| `TERMINAL_ID_RISK_7DAY_WINDOW` | **0.1567** | 🟡 MODERATE | 0.54 ± 0.41 | 0.59 ± 0.38 |
| `TERMINAL_ID_NB_TX_7DAY_WINDOW` | **0.0809** | 🟢 STABLE | 15.06 ± 8.07 | 13.56 ± 7.09 |
| `CUSTOMER_ID_NB_TX_30DAY_WINDOW` | **0.0802** | 🟢 STABLE | 83.39 ± 31.22 | 81.57 ± 30.57 |
| `CUSTOMER_ID_NB_TX_7DAY_WINDOW` | **0.0712** | 🟢 STABLE | 20.18 ± 8.12 | 19.41 ± 7.84 |
| `CUSTOMER_ID_AVG_AMOUNT_7DAY_WINDOW` | **0.0706** | 🟢 STABLE | 136.11 ± 171.66 | 149.84 ± 190.64 |
| `TERMINAL_ID_RISK_1DAY_WINDOW` | **0.0555** | 🟢 STABLE | 0.55 ± 0.46 | 0.58 ± 0.45 |
| `CUSTOMER_ID_AVG_AMOUNT_1DAY_WINDOW` | **0.0507** | 🟢 STABLE | 144.07 ± 258.38 | 141.53 ± 173.22 |
| `TERMINAL_ID_NB_TX_1DAY_WINDOW` | **0.0497** | 🟢 STABLE | 3.11 ± 1.83 | 2.80 ± 1.63 |
| `TERMINAL_ID_NB_TX_30DAY_WINDOW` | **0.0471** | 🟢 STABLE | 55.91 ± 29.81 | 57.38 ± 28.81 |
| `TX_AMOUNT_ZSCORE` | **0.0361** | 🟢 STABLE | 0.15 ± 1.29 | 0.12 ± 1.25 |
| `TX_AMOUNT` | **0.0150** | 🟢 STABLE | 150.15 ± 445.93 | 136.63 ± 276.96 |
| `CUSTOMER_ID_NB_TX_1DAY_WINDOW` | **0.0099** | 🟢 STABLE | 3.76 ± 1.98 | 3.71 ± 1.88 |
| `TX_DIST_CUSTOMER_TERMINAL` | **0.0053** | 🟢 STABLE | 1.13 ± 1.72 | 1.19 ± 1.74 |
| `TIME_SINCE_LAST_TX` | **0.0043** | 🟢 STABLE | 43738.85 ± 72128.92 | 43498.29 ± 71614.42 |
| `CUSTOMER_ID_NB_TX_1HOUR_WINDOW` | **0.0010** | 🟢 STABLE | 1.13 ± 0.37 | 1.14 ± 0.38 |
| `TX_DURING_WEEKEND` | **0.0000** | 🟢 STABLE | 0.24 ± 0.43 | 0.20 ± 0.40 |
| `TX_DURING_NIGHT` | **0.0000** | 🟢 STABLE | 0.13 ± 0.34 | 0.14 ± 0.35 |
| `CUSTOMER_ID_NB_TX_15MIN_WINDOW` | **0.0000** | 🟢 STABLE | 1.04 ± 0.19 | 1.04 ± 0.19 |

---

## 🛠️ Automated Retraining Policy
1. **Trigger Condition:** If $\ge 2$ core features exceed $\text{PSI} > 0.25$ OR prediction score $\text{PSI} > 0.25$, initiate automated walk-forward retraining (`python -m src.train --cv`).
2. **Data Pipeline Action:** If terminal risk or distance metrics drift, verify upstream geolocation lookups and feature windowing latency.
