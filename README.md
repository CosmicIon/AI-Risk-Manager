# AI Risk Manager: Fraud Detection System

**Goal:** Stop merchants from losing money to card-not-present fraud by building a working, defense-only fraud detector.

## The Problem
AI-enabled fraud is hitting the BFSI sector, while returns and chargebacks quietly eat into margins. Without detection, a merchant loses the full transaction amount plus chargeback fees for every fraudulent transaction. However, blindly flagging every transaction creates massive friction for legitimate customers and burdens manual review teams with false positives. The goal is to accurately detect fraud while minimizing the total cost to the business.

## The Approach
This project implements a linear, robust machine learning pipeline trained on a dataset of 1.75 million simulated transactions (from the [Fraud Detection Handbook](https://fraud-detection-handbook.github.io/fraud-detection-handbook/)).

1. **Features:** We engineered customer-level and terminal-level rolling statistics (1, 7, and 30-day windows). To avoid future data leakage, terminal risk scores strictly use labels delayed by 7 days.
2. **Splitting:** We use a time-based split. The model trains on earlier data (May-July) and predicts on later data (August-September) with a gap in between to ensure no temporal overlap or label leakage.
3. **Model:** We trained an industry-standard **LightGBM** gradient-boosted tree. Because fraud is extremely rare (<1%), we do not use accuracy (which would be 99%+ for a model that does nothing). Instead, we optimize for **Precision-Recall AUC (PR-AUC)** and use `scale_pos_weight` to handle class imbalance without introducing synthetic data leakage (like SMOTE).
4. **Explainability:** We wrapped the model with a SHAP-based explainer that produces plain-English, defense-only sentences (e.g., "This amount is unusual for this customer") so a non-technical merchant can understand exactly why a transaction was flagged.

## The Results
On the held-out test set spanning ~550,000 transactions:
- **No-skill Baseline (Flag Nothing):** Costs the merchant **$624,998.93** in undetected fraud.
- **Naive Baseline (Flag Everything):** Costs **$2,729,390.00** in false positive friction and manual reviews.
- **Our LightGBM Model:** Achieves a PR-AUC of **0.79** and reduces the total expected cost to **$156,178.55**.

This represents a **75% reduction in fraud losses and manual review costs** compared to doing nothing, saving the merchant ~$468k over just a two-month period.

*(Detailed charts, PR curves, and confusion matrices are available in the `reports/figures/` directory).*

## How to Run It

The following instructions are designed for Windows PowerShell.

### 1. Setup Environment
First, create a virtual environment and install the required packages:
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the Full Data and Training Pipeline
The pipeline is completely modular. You must run these scripts sequentially to generate the simulated data, build the features, and train the model:
```powershell

.\venv\Scripts\python -m src.ingestion
.\venv\Scripts\python -m src.eda
.\venv\Scripts\python -m src.features
.\venv\Scripts\python -m src.split
.\venv\Scripts\python -m src.train
.\venv\Scripts\python -m src.evaluate
.\venv\Scripts\python -m src.explain




.\venv\Scripts\python -m src.ingestion
.\venv\Scripts\python -m src.features
.\venv\Scripts\python -m src.split
.\venv\Scripts\python -m src.train
.\venv\Scripts\python -m src.evaluate
```
*(Note: Generating 1.7 million transactions and computing rolling windows will take about 5-8 minutes depending on your hardware).*

### 3. Run the Dashboard
To see the model in action and view the defense-only explainability:
```powershell
.\venv\Scripts\streamlit run src\dashboard.py
```

### 4. Run the Smoke Test
If you want to quickly verify that the pipeline runs end-to-end without errors, you can run the smoke test (which temporarily overrides the config to use a tiny 60-day dataset):
```powershell
.\venv\Scripts\pytest tests\test_pipeline_smoke.py
```

## Next Steps (If I Had More Time)
1. **Graph-based features:** Map networks of customers and terminals to catch coordinated fraud rings (e.g., "this customer suddenly started using a terminal cluster associated with past fraud").
2. **Real-time streaming inference:** Move the feature computation to an event-driven architecture (e.g., Kafka + Redis online feature store) so risk scores are returned synchronously during checkout.
3. **Active Learning Loop:** Build a feedback mechanism where an analyst's decision (True Positive or False Positive) is fed back into a rolling model retrain.
4. **Sequence Models:** Use LSTMs or Transformers to learn the sequence of a customer's temporal behavior instead of relying solely on aggregated windows.

---
**Defense-Only Policy:** This system is built strictly for defense. It scores, flags, and explains risk. It does not output adversarial examples, evasion techniques, or anything that could be repurposed to bypass scoring systems. Explanations are intentionally phrased from the defender's perspective to assist human investigators.
