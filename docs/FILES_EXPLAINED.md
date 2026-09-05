# 🎓 AI Risk Manager: Complete File-by-File Guide (For Judges & Demos)

This document is your **cheat sheet** to explain every single file in the project to a hackathon or technical judge.

Each file has:
1. **In Simple Words:** What the file actually does.
2. **Everyday Analogy:** A real-world comparison anyone can understand.
3. **🎤 What to Say to the Judge:** The exact 10-second punchline to explain it smoothly.
4. **💡 The "Secret Sauce":** The smart technical detail that will impress them.

---

## ⚡ 60-Second Elevator Pitch (Memorize This!)

> *"Most fraud detection projects stop at basic machine learning with toy 50% cutoffs that don't work in banks. **AI Risk Manager** is a complete, production-grade fraud operations platform. It takes raw transactions, engineers real-time behavioral features with zero future data leakage, trains an ultra-fast LightGBM model, and routes transactions through a **3-tier triage system** (Approve / OTP Challenge / Decline) in under 15 milliseconds. It even translates complex math into plain English for non-technical investigators and monitors live data drift over time."*

---

## 🗂️ Table of Contents
1. [Core Engine Files (`src/`)](#1-core-engine-files-src)
2. [Dataset Adapters (`src/adapters/`)](#2-dataset-adapters-srcadapters)
3. [Configuration & Infrastructure](#3-configuration--infrastructure)
4. [Enterprise Test Suite (`tests/`)](#4-enterprise-test-suite-tests)
5. [Top 5 Toughest Judge Questions & How to Answer Them](#5-top-5-toughest-judge-questions--how-to-answer-them)

---

## 1. Core Engine Files (`src/`)

### 1. `src/ingestion.py` — The Realistic Transaction Generator
* **In Simple Words:** Creates 180 days of realistic card transactions (1.75+ million purchases) and injects realistic criminal attacks.
* **Everyday Analogy:** A flight simulator for pilots, but for bank card transactions.
* **🎤 What to Say to the Judge:**  
  > *"We simulate 10,000 customers shopping across 20,000 terminals with spatial coordinates and Poisson purchase intervals. Then we inject three real-world fraud patterns: high-value spikes, compromised terminals, and stolen card spending bursts."*
* **💡 The "Secret Sauce":** It doesn't generate random nonsense—customers have geographic homes and typical daily spending habits, so fraud looks like genuine behavioral anomalies.

---

### 2. `src/features.py` — The Detective's Clue Finder
* **In Simple Words:** Takes raw transaction receipts (Who, When, Where, How Much) and extracts 21 smart behavioral clues.
* **Everyday Analogy:** A detective looking into a suspect's history: *"Does Alice normally spend this much? Has she ever shopped in this city before?"*
* **🎤 What to Say to the Judge:**  
  > *"Raw numbers aren't enough. We engineer 21 features including rolling 15-minute burst velocity, 2D customer-to-terminal distance, per-customer Z-scores, and 7-day lagged terminal risk."*
* **💡 The "Secret Sauce":** The **7-Day Lagged Terminal Risk**. In the real world, fraud reports take about a week to reach the bank. If you use today's fraud reports to predict today's fraud, you are cheating (data leakage). We enforce a strict 7-day delay.

---

### 3. `src/split.py` — The Time-Safe Dataset Splitter
* **In Simple Words:** Splits data into past transactions (Training) and future transactions (Testing), with a mandatory 7-day safety buffer in between.
* **Everyday Analogy:** Studying last semester's textbooks to prepare for this semester's exam, making sure you don't accidentally see the exam answers in advance.
* **🎤 What to Say to the Judge:**  
  > *"Traditional random K-fold splits are flawed in financial fraud because future information leaks into the past. We use a chronological time split with an explicit 7-day embargo cooling buffer."*
* **💡 The "Secret Sauce":** The **7-Day Embargo Buffer**. We throw away the 7 days between training and testing so unresolved chargebacks can't corrupt the boundary.

---

### 4. `src/train.py` — The AI Brain Builder
* **In Simple Words:** Trains an ultra-fast **LightGBM** machine learning model to distinguish between normal spending and fraud.
* **Everyday Analogy:** Teaching a guard dog to recognize the scent of danger among thousands of normal visitors.
* **🎤 What to Say to the Judge:**  
  > *"Because fraud accounts for less than 1% of transactions, standard models get lazy and predict 'No Fraud' every time. We use class-weighted LightGBM (`scale_pos_weight`) so the model prioritizes catching rare fraud signals."*
* **💡 The "Secret Sauce":** We also train a baseline Logistic Regression model alongside LightGBM to mathematically prove how much tree-based boosting outperforms simple linear baselines.

---

### 5. `src/cross_validate.py` — The Time-Travel Validator
* **In Simple Words:** Tests the model across multiple expanding time windows to prove it won't fail next month.
* **Everyday Analogy:** Testing a car not just on a sunny day, but in rain, snow, and gravel over months.
* **🎤 What to Say to the Judge:**  
  > *"We implemented a 3-fold Walk-Forward Purged Cross-Validation. Each fold trains on past months and tests on future months with embargo buffers, proving our model doesn't overfit a single lucky time window."*
* **💡 The "Secret Sauce":** Walk-forward cross-validation is the gold standard used by quantitative hedge funds and major banks.

---

### 6. `src/tune.py` — The Automated AI Optimizer (Optuna)
* **In Simple Words:** Uses AI search algorithms to automatically test dozens of model settings and pick the winning combination.
* **Everyday Analogy:** A master audio engineer fine-tuning dials on a soundboard to get crystal-clear sound.
* **🎤 What to Say to the Judge:**  
  > *"Instead of guessing hyperparameters, we use Optuna with Bayesian optimization (TPE) to find the best tree depth, learning rate, and class weights, specifically maximizing PR-AUC on temporal validation splits."*
* **💡 The "Secret Sauce":** We optimize for **PR-AUC** (Precision-Recall Area Under Curve), NOT ROC-AUC, because ROC-AUC is misleadingly optimistic on heavily imbalanced datasets.

---

### 7. `src/evaluate.py` — The Business Dollar Calculator
* **In Simple Words:** Calculates how much real money the bank saves and finds the optimal decision cutoff based on dollars, not guesses.
* **Everyday Analogy:** Weighing the cost of a false fire alarm ($5) against the cost of letting a building burn down ($128).
* **🎤 What to Say to the Judge:**  
  > *"A 50% probability threshold is financially naive. We run a 99-step cost sweep balancing the $5 cost of checking an innocent customer against the $128 cost of a stolen chargeback. Our optimal threshold ($t^* = 0.78$) cuts total fraud losses by over 74%."*
* **💡 The "Secret Sauce":** It connects pure machine learning math directly to **P&L (Profit and Loss)** balance sheets.

---

### 8. `src/explain.py` — The Plain-English Translator (XAI)
* **In Simple Words:** Takes complex SHAP mathematics and translates it into clear English sentences for fraud investigators.
* **Everyday Analogy:** A doctor translating an MRI scan into simple advice: *"Your knee hurts because of this specific ligament."*
* **🎤 What to Say to the Judge:**  
  > *"Investigators don't have time to decipher mathematical vectors. Our explainability engine maps top SHAP values directly into plain-English defense narratives, such as 'Amount is 5x higher than normal and store is 150 miles away'."*
* **💡 The "Secret Sauce":** **Defense-Only Compliance**. The engine only explains why a transaction is protected or suspicious; it never provides tips on how a fraudster could bypass the system.

---

### 9. `src/api.py` — The Real-Time Gateway Microservice (FastAPI)
* **In Simple Words:** A lightning-fast web service that scores transactions in under 15 milliseconds during checkout.
* **Everyday Analogy:** The electronic turnstile at a metro station that checks your ticket and opens or locks in a split second.
* **🎤 What to Say to the Judge:**  
  > *"In payments, decisions must happen in under 50 milliseconds. Our FastAPI microservice uses an in-memory feature cache to calculate spatial distance, burst velocity, and model scores in less than 15 milliseconds, returning a 3-tier triage verdict."*
* **💡 The "Secret Sauce":** The **3-Tier Triage Action**:
  1. `APPROVE` (Frictionless checkout)
  2. `CHALLENGE` (Send SMS/App OTP—recovers revenue without losing customers!)
  3. `DECLINE` (Hard block)

---

### 10. `src/dashboard.py` — The Executive Cockpit (Streamlit)
* **In Simple Words:** An interactive visual command center for risk managers to monitor live fraud, test threshold sliders, and adjust unit costs.
* **Everyday Analogy:** The air-traffic control radar room for an entire airport.
* **🎤 What to Say to the Judge:**  
  > *"Our dashboard gives executives a live verdict, ROI metrics, a real-time flagged transaction feed with SHAP waterfalls, and a 60 FPS dual-threshold simulator where business users can adjust cost assumptions in real time."*
* **💡 The "Secret Sauce":** The live interactive cost sliders—judges can change the cost of a false alarm from $5 to $20 and watch the entire business ROI update instantly.

---

### 11. `src/drift.py` — The System Health Monitor (PSI)
* **In Simple Words:** Regularly checks if customer spending habits or fraud tricks have changed over time.
* **Everyday Analogy:** A regular blood test that warns you of health changes before you get sick.
* **🎤 What to Say to the Judge:**  
  > *"Machine learning models decay as fraud patterns evolve. We compute the Population Stability Index (PSI) across all 21 features. If PSI exceeds 0.25, the system automatically alerts the team that retraining is required."*
* **💡 The "Secret Sauce":** Tracks both **Data Drift** (how customer inputs change) and **Concept Drift** (how fraudster tactics change).

---

### 12. `src/eda.py` — The Data Investigator
* **In Simple Words:** Analyzes raw transactions, calculates fraud percentages, and draws charts of spending distributions.
* **Everyday Analogy:** An accountant doing an initial audit of bank books before building a new software system.
* **🎤 What to Say to the Judge:**  
  > *"Generates exploratory data analysis reports and charts showing transaction amounts, night vs. day patterns, and scenario distributions."*

---

### 13. `src/utils.py` — The Helper Toolkit
* **In Simple Words:** Small helper functions that load YAML settings and manage file paths safely.
* **Everyday Analogy:** The toolbox with wrenches and screwdrivers that every mechanic keeps handy.
* **🎤 What to Say to the Judge:**  
  > *"Centralizes configuration loading and path resolution so the entire pipeline runs consistently on Windows, Linux, and macOS."*

---

## 2. Dataset Adapters (`src/adapters/`)

### 14. `src/adapters/base.py` — The Universal Blueprint
* **In Simple Words:** Defines the standard interface that all dataset loaders must follow.
* **🎤 What to Say to the Judge:**  
  > *"An abstract base class ensuring that any external bank dataset is transformed into our standardized schema before entering the pipeline."*

### 15. `src/adapters/kaggle.py` & `src/adapters/ieee_cis.py` — The Benchmark Adapters
* **In Simple Words:** Plug-and-play converters that allow our system to train and run on world-famous public fraud datasets (Kaggle Credit Card & IEEE-CIS).
* **Everyday Analogy:** An international power adapter that lets an American plug work in a European outlet.
* **🎤 What to Say to the Judge:**  
  > *"We didn't just build this for simulated data. We wrote plug-and-play adapters for standard industry benchmarks like Kaggle and IEEE-CIS, proving our architecture is dataset-agnostic."*

---

## 3. Configuration & Infrastructure

### 16. `config.yaml` — The Central Steering Wheel
* **In Simple Words:** One single file where all settings, dollar costs, and hyperparameters live.
* **Everyday Analogy:** The settings menu in a smartphone where you control everything in one place.
* **🎤 What to Say to the Judge:**  
  > *"No magic numbers are hardcoded in the codebase. Everything—from simulation sizes and rolling window hours to financial review costs—is configured declaratively in `config.yaml`."*

### 17. `Makefile` — The One-Click Automator
* **In Simple Words:** Simple command shortcuts to run the entire pipeline, start the API, or run tests with one word.
* **🎤 What to Say to the Judge:**  
  > *"Provides single-command automation: `make run` executes the entire pipeline, `make api` starts the microservice, and `make test` verifies the system."*

### 18. `ARCHITECTURE.md` & `README.md` — The Blueprints
* **In Simple Words:** Comprehensive production engineering documentation with Mermaid diagrams, mathematical formulas, and quickstart guides.

---

## 4. Enterprise Test Suite (`tests/`)

The repository includes **35 automated tests** running on **GitHub Actions CI**. Here is what each test file proves:

| Test File | What it Proves to the Judge |
| :--- | :--- |
| **`tests/test_api.py`** | Proves the FastAPI endpoint responds in $<50\text{ms}$ and correctly returns 3-tier decisions. |
| **`tests/test_leakage.py`** | **Critical:** Mathematically proves zero future lookahead leakage and enforces the 7-day delayed feedback rule. |
| **`tests/test_validation.py`** | Verifies walk-forward expanding windows and embargo buffers never overlap. |
| **`tests/test_tune.py`** | Proves Optuna parameter boundaries and objective functions execute cleanly. |
| **`tests/test_drift.py`** | Proves PSI math detects zero-shift stability and alerts on simulated feature drift. |
| **`tests/test_adapters.py`** | Tests schema conversion and 2D spatial distance calculation. |
| **`tests/test_triage.py`** | Validates the 3-tier triage boundaries (`APPROVE`, `CHALLENGE`, `DECLINE`) and OTP recovery logic. |
| **`tests/test_features.py`** | Tests per-customer Z-score variance, sub-hour burst velocity, and distance calculations. |
| **`tests/test_pipeline_smoke.py`** | End-to-end integration smoke test running the full pipeline on a miniature dataset in seconds. |

---

## 5. Top 5 Toughest Judge Questions & How to Answer Them

### ❓ Q1: "Why did you use LightGBM instead of Deep Learning (like an LSTM or Transformer)?"
> **Your Winning Answer:**  
> *"In payment gateway inference, latency is strictly capped at under 50 milliseconds. LightGBM on tabular financial features consistently outperforms deep neural nets on tabular data, trains 20x faster, evaluates in microseconds, and natively provides tree-based SHAP explainability required by financial regulators."*

---

### ❓ Q2: "Why not use standard 5-fold cross-validation?"
> **Your Winning Answer:**  
> *"Because random K-fold shuffling in time-series data is a critical error. It causes lookahead leakage—the model uses tomorrow's customer spending to predict yesterday's fraud. We implemented Walk-Forward Purged Cross-Validation with a 7-day embargo buffer to reflect real banking operations where chargebacks take days to resolve."*

---

### ❓ Q3: "What makes your 3-tier triage better than normal binary flag/clear?"
> **Your Winning Answer:**  
> *"Binary systems either approve or decline. If you decline all suspicious purchases, you infuriate legitimate customers and lose sales. Our middle tier (`CHALLENGE`) sends an instant SMS OTP. Legitimate cardholders verify in 5 seconds and complete the purchase, while fraudsters holding stolen credentials are stopped dead. This recovers significant merchant revenue."*

---

### ❓ Q4: "How do you choose your decision threshold?"
> **Your Winning Answer:**  
> *"Instead of picking an arbitrary 0.5 threshold, we minimize an exact business cost function:  
> `Total Cost = (False Positives * $5.00 review cost) + (False Negatives * Average Fraud Amount)`.  
> We evaluate 99 cutoffs to mathematically locate the threshold that minimizes dollar loss."*

---

### ❓ Q5: "How does your system know when the model is getting outdated?"
> **Your Winning Answer:**  
> *"We built `src/drift.py`, which computes the Population Stability Index (PSI) between training baselines and live production transactions. If PSI exceeds 0.25 on key features like spending Z-score or velocity, an automated alert triggers to retrain the model."*
