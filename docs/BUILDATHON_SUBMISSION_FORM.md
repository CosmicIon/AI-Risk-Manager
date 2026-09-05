# 📋 Razorpay Buildathon Submission Answers (Copy-Paste Ready)

Use these polished, high-impact responses to fill out your Google Form.

---

### Field 1: Project Name / Title *

```text
AI Risk Manager: Real-Time Fraud Defense & 3-Tier Risk Triage for Modern Payment Gateways
```

---

### Field 2: Project Objectives (What does it solve?) *

```text
Across Indian digital payments and e-commerce, merchants are trapped in a costly dilemma: aggressive fraud filters cause checkout abandonment by declining honest customers, while lax rules lead to margin-destroying chargeback penalties. Traditional machine learning solutions fail in production because they rely on binary (Flag/Decline) decisions and suffer from multi-second latency.

AI Risk Manager solves this through an end-to-end, defense-only fraud mitigation platform:
1. 3-Tier Risk Triage (Approve / OTP Challenge / Decline): Rather than auto-declining suspicious orders, medium-risk transactions trigger an instant SMS/WhatsApp OTP step-up verification (standard in Indian BFSI/3DS). Legitimate customers verify in seconds, while fraudsters with stolen cards are stopped, recovering substantial merchant revenue.
2. Sub-15ms Real-Time Inference: A production FastAPI microservice with an in-memory feature cache calculates 21 behavioral, spatial, and burst-velocity signals in under 15 milliseconds, comfortably beating payment gateway sub-50ms latency SLAs.
3. Cost-Sensitive Business Optimization: Replaces arbitrary 0.5 thresholds with an empirical cost-utility function balancing false alarm review costs ($5) against chargeback losses ($128). The optimal threshold cuts merchant fraud losses by 74% ($491,816 net savings on held-out test data) while frictionlessly clearing 99.4% of legitimate volume.
4. Human-Centric Explainability (XAI): Translates SHAP feature attributions into plain-English defense narratives so frontline investigators and merchants instantly understand why an order was flagged.
```

---

### Field 3: GitHub Repository URL *

```text
https://github.com/CosmicIon/AI-Risk-Manager
```

---

### Field 4: 5-min Pitch Video Link *

```text
[Paste your Loom / YouTube (Unlisted) / Google Drive video link here]
```

*(Tip: Upload your recording as an **Unlisted** YouTube video or share a **Loom** link. Ensure permission is set to "Anyone with the link can view").*

---

### Field 5: Build Challenges & Technical Obstacles (What issues did you face while building, and how did you solve them?) *

```text
1. Temporal Lookahead Data Leakage:
- Challenge: In financial fraud, chargebacks take 7 to 14 days to be confirmed by banks. Traditional random K-fold cross-validation uses future chargeback labels to predict past fraud, creating artificially inflated accuracy that collapses in production.
- Solution: We enforced strict temporal integrity: terminal fraud risk features incorporate a mandatory 7-day delayed feedback loop, dataset splitting implements a 7-day purged embargo cooling buffer, and validation uses a 3-fold expanding walk-forward cross-validation.

2. Severe Class Imbalance (<1% Fraud Rate):
- Challenge: Legitimate transactions represent >99.3% of traffic. Standard models become lazy, predicting "No Fraud" to achieve 99% accuracy while letting criminals drain balances.
- Solution: We discarded ROC-AUC in favor of PR-AUC (Precision-Recall Area Under Curve), integrated class-imbalance reweighting (scale_pos_weight) in LightGBM, and used Optuna Bayesian optimization (TPE) to tune tree hyperparameters against out-of-time validation splits.

3. Sub-50ms Production Latency SLA:
- Challenge: Real-time checkout gateways cannot wait for heavy SQL queries calculating 30-day historical aggregates over millions of records.
- Solution: We engineered an InMemoryFeatureStore within FastAPI using dual deques and hash tables, combined with vectorized 2D spatial distance computations. This compressed end-to-end feature extraction and model scoring to under 15ms.

4. Model Degradation Over Time (Concept Drift):
- Challenge: Fraudsters continuously alter attack tactics, rendering static models obsolete within weeks.
- Solution: We built an automated drift monitor (src/drift.py) computing the Population Stability Index (PSI) across all 21 features. When PSI exceeds 0.25, the system automatically triggers alerts recommending scheduled model retraining.
```
