# AI Risk Manager — Product Requirements Document

## 1. System Overview & Objectives

### 1.1 Business Value

Indian BFSI (Banking, Financial Services, and Insurance) is losing ₹thousands of crores annually to three interconnected leakage vectors:

| Loss Vector | Estimated Annual Impact (Indian Market) | Current Detection Gap |
|---|---|---|
| **Chargebacks** | ₹2,800 Cr+ across card networks | <40% representment win rate; most merchants don't even respond |
| **Return Abuse** | ₹1,200 Cr+ in e-commerce alone | Treated as cost-of-doing-business; almost zero ML adoption |
| **Transaction Fraud** | ₹4,600 Cr+ (RBI FY25 data) | Rule-based systems miss AI-enabled synthetic identity fraud |
| **Abuse Rings** | Unquantified (hidden in other categories) | Graph-based patterns invisible to row-level ML models |

**AI Risk Manager** is a production-grade platform that detects, scores, and responds to these loss events with measured precision and recall — with every decision carrying an explicit false-positive cost estimate.

### 1.2 Core Problem Solved

Merchants and financial institutions lack a unified, ML-driven system to:
1. **Detect** fraud spikes and abuse rings in real-time transaction streams.
2. **Score** return requests for abuse probability at the point of decision.
3. **Respond** to chargebacks with AI-assembled evidence packages that meet card network formatting requirements.
4. **Measure** all of the above with honest, cost-weighted metrics on held-out test sets.

### 1.3 Primary User Personas

| Persona | Role | Key Need |
|---|---|---|
| **Risk Analyst** | Reviews flagged transactions, makes accept/reject decisions | Low false-positive rate; clear explanations for every flag |
| **Chargeback Specialist** | Handles dispute representment within network deadlines | Auto-generated evidence packages; deadline tracking |
| **Merchant / Platform Owner** | Oversees P&L impact of risk decisions | Dashboard with cost-weighted metrics; ROI visibility |
| **ML Engineer** | Maintains and retrains models | Evaluation pipeline; model versioning; drift alerts |
| **Compliance Officer** | Ensures RBI/PCI-DSS compliance | Audit trails; data localization proof; defense-only attestation |

---

## 2. Functional Requirements

### 2.1 Module 1 — Chargeback Evidence Responder (Primary)

| ID | Requirement | Input | Output | Priority |
|---|---|---|---|---|
| CB-01 | Ingest chargeback notifications from card networks (Visa TC40/SAFE, Mastercard ALERT, RuPay) via webhook or file upload | Network notification payload (JSON/ISO 8583) | Parsed chargeback case record | P0 |
| CB-02 | Extract dispute reason code and map to evidence requirements | Reason code + network identifier | Evidence checklist (e.g., delivery proof, AVS match, 3DS log) | P0 |
| CB-03 | AI agent retrieves relevant evidence from merchant systems (order DB, shipping API, payment gateway logs, customer communications) | Case ID + evidence checklist | Structured evidence bundle | P0 |
| CB-04 | LLM generates representment narrative tailored to the specific reason code and card network formatting rules | Evidence bundle + reason code + network template | Draft representment letter (PDF/structured text) | P0 |
| CB-05 | Confidence scorer evaluates win probability for the assembled response | Complete evidence package | Win probability (0-1) + recommendation (respond/accept loss) | P0 |
| CB-06 | Human-in-the-loop review queue with approve/edit/reject workflow | Draft response + win probability | Final submitted response | P0 |
| CB-07 | Track representment outcome (won/lost) and feed back into model training | Network resolution notification | Updated training dataset + model performance metrics | P1 |
| CB-08 | Deadline tracker with escalation alerts (Visa: 30 days, Mastercard: 45 days) | Case creation timestamp + network | Countdown timer + escalation notifications | P0 |

### 2.2 Module 2 — Return-Risk Scorer

| ID | Requirement | Input | Output | Priority |
|---|---|---|---|---|
| RT-01 | Real-time scoring of return/refund requests at the point of initiation | Customer ID, order details, return reason, historical behavior | Risk score (0-100) + risk tier (low/medium/high/critical) | P0 |
| RT-02 | Feature computation: return frequency, value patterns, category concentration, account age, device fingerprint | Raw transaction + customer history | Feature vector (≤50 features) | P0 |
| RT-03 | Policy engine that maps risk tiers to actions (auto-approve, manual review, auto-deny with explanation) | Risk score + merchant-configured thresholds | Decision + customer-facing explanation | P0 |
| RT-04 | Batch retraining pipeline with stratified holdout evaluation | Historical returns dataset (labeled: legitimate vs. abusive) | Updated model + evaluation report | P1 |

### 2.3 Module 3 — Fraud-Spike Detector

| ID | Requirement | Input | Output | Priority |
|---|---|---|---|---|
| FD-01 | Streaming anomaly detection over transaction velocity, amount distribution, and geographic spread | Real-time transaction stream | Anomaly flag + severity + affected segment | P0 |
| FD-02 | Distinguish genuine volume spikes (festivals, sales events) from attack patterns using contextual features (calendar, merchant category, historical baselines) | Transaction stream + contextual metadata | Classification: organic_spike vs. attack vs. uncertain | P0 |
| FD-03 | Alert routing with configurable severity thresholds and notification channels (email, Slack, PagerDuty, SMS) | Anomaly detection output | Routed alert with full context | P1 |

### 2.4 Module 4 — Abuse-Ring Sentinel

| ID | Requirement | Input | Output | Priority |
|---|---|---|---|---|
| AR-01 | Build and maintain a transaction graph linking entities: buyers, sellers, shipping addresses, device fingerprints, payment instruments | Transaction stream | Evolving entity graph | P1 |
| AR-02 | Community detection to identify suspicious clusters (shared addresses, device reuse, coordinated timing) | Entity graph | Detected communities + suspicion scores | P1 |
| AR-03 | Alert on newly formed rings with evidence visualization (subgraph rendering) | Community detection output | Ring alert + visual subgraph + narrative explanation | P2 |

### 2.5 Cross-Cutting Features

| ID | Requirement | Priority |
|---|---|---|
| CC-01 | Unified case management system across all modules with status tracking, assignment, and audit trail | P0 |
| CC-02 | Cost-weighted metrics dashboard: precision, recall, F1, and explicit ₹-denominated false-positive cost and false-negative cost | P0 |
| CC-03 | Model evaluation pipeline that runs on every model update against a versioned held-out test set | P0 |
| CC-04 | Explainability layer: every ML decision must carry a human-readable explanation (SHAP values for tabular, attention highlights for LLM) | P0 |
| CC-05 | Role-based access control (RBAC) with audit logging | P0 |
| CC-06 | Multi-tenant support for serving multiple merchants from a single deployment | P1 |

---

## 3. Non-Functional Requirements

### 3.1 Latency Budgets

| Operation | P50 Target | P99 Target | Hard Ceiling |
|---|---|---|---|
| Return-risk score (real-time API) | ≤ 50ms | ≤ 150ms | 300ms (timeout) |
| Fraud-spike detection (stream processing) | ≤ 500ms from event ingestion | ≤ 2s | 5s |
| Chargeback evidence assembly (async) | ≤ 30s | ≤ 120s | 300s (5 min) |
| Abuse-ring community detection (batch) | ≤ 5 min per graph snapshot | ≤ 15 min | 30 min |
| Dashboard API responses | ≤ 100ms | ≤ 500ms | 1s |

### 3.2 Throughput & Concurrency

| Metric | Target |
|---|---|
| Peak transaction ingestion rate | 10,000 TPS (to handle festival spikes) |
| Concurrent return-risk scoring requests | 1,000 RPS |
| Concurrent chargeback processing pipelines | 100 parallel cases |
| Dashboard concurrent users | 200 |

### 3.3 Availability & Reliability

| Metric | Target |
|---|---|
| System uptime (return scorer, fraud detector) | 99.95% (≤ 22 min/month downtime) |
| System uptime (chargeback responder, ring sentinel) | 99.9% (≤ 44 min/month downtime) |
| Data durability | 99.999999% (8 nines) |
| RPO (Recovery Point Objective) | ≤ 1 minute |
| RTO (Recovery Time Objective) | ≤ 5 minutes |

### 3.4 Security & Compliance

| Requirement | Details |
|---|---|
| **RBI Data Localization** | All financial data must be stored and processed within India. No cross-border data transfer without explicit consent and regulatory approval. |
| **PCI-DSS Level 1** | Card data (PAN, CVV) must never be stored; only tokenized references permitted. |
| **Defense-Only Constraint** | System must not expose any capability that could be used offensively (e.g., no fraud generation, no synthetic identity creation, no transaction spoofing). All model endpoints are inference-only with no ability to generate adversarial examples. |
| **Encryption** | AES-256 at rest, TLS 1.3 in transit. |
| **Audit Trail** | Every decision, model inference, and data access logged with immutable timestamps. |
| **Data Retention** | Chargeback records: 7 years (as per card network rules). Transaction data: 10 years (RBI mandate). |

### 3.5 Rate Limits & Quotas

| Resource | Limit |
|---|---|
| LLM API calls (per tenant, per hour) | 500 (chargeback evidence generation) |
| Return scoring API (per tenant, per second) | 100 |
| Dashboard API (per user, per minute) | 120 |
| Webhook ingestion (per source, per second) | 500 |

---

## 4. Failure Modes & Edge Cases

### 4.1 Model Degradation & Drift

| Failure Mode | Detection | Mitigation |
|---|---|---|
| **Feature drift** (input distribution shift, e.g., new payment method adoption) | KL-divergence monitoring on feature distributions, per-feature PSI (Population Stability Index) | Alert at PSI > 0.1; auto-trigger retraining pipeline at PSI > 0.2 |
| **Label drift** (change in fraud patterns) | Precision/recall degradation on rolling evaluation window | Shadow scoring with challenger model; gradual traffic shift |
| **LLM quality degradation** (provider model update changes output format) | Structured output validation (JSON schema checks on every LLM response) | Fallback to template-based evidence assembly; alert ML team |
| **Stale features** (feature store lag) | Feature freshness monitoring (max staleness per feature) | Serve with degraded feature set + reduced confidence; flag for review |

### 4.2 Infrastructure Failures

| Failure Mode | Detection | Mitigation |
|---|---|---|
| **Message queue backlog** (Kafka consumer lag) | Consumer lag monitoring per partition | Auto-scale consumers; alert at >10s lag; circuit-break at >60s |
| **Database failover** | Health check probes + replication lag monitoring | Automatic failover to read replica; promote replica if primary unrecoverable |
| **LLM API rate limit / timeout** | HTTP 429/504 response codes | Exponential backoff with jitter; request queue with priority (deadline-based); fallback to smaller/local model |
| **Feature store unavailability** | Health probes | Serve with cached features (stale but available); reduced confidence flag |

### 4.3 Business Logic Edge Cases

| Edge Case | Handling |
|---|---|
| **Chargeback for a transaction older than merchant records** | Flag as "insufficient evidence"; recommend accepting the loss; log for future data retention policy review |
| **Return request with risk score exactly at threshold boundary** | Apply merchant-configured tie-breaking rule (default: route to manual review) |
| **Fraud spike during a known sale event** | Calendar-aware baseline adjustment; require higher anomaly threshold during pre-registered events |
| **Abuse ring spanning multiple tenants** | Cross-tenant graph analysis only with explicit data-sharing agreements; otherwise, per-tenant detection only |
| **Conflicting signals** (high risk score but high-value loyal customer) | Surface both signals to analyst with full context; never auto-deny high-lifetime-value customers without human review |
| **Duplicate chargeback notifications** | Idempotency key on (network + ARN/case_id); deduplicate at ingestion |
| **Model produces prediction outside calibrated range** | Clamp to [0, 1]; log as anomaly; trigger model health check |

### 4.4 Adversarial Robustness (Defense-Only Constraint)

| Threat | Mitigation |
|---|---|
| **Prompt injection in chargeback dispute text** | Input sanitization; LLM operates in a sandboxed tool-use mode with no access to system internals |
| **Adversarial feature manipulation** (attacker crafts transactions to evade scoring) | Ensemble models with diverse feature sets; adversarial training on held-out attack patterns |
| **Data poisoning** (attacker submits false labels via dispute outcomes) | Label quality monitoring; anomaly detection on label distribution; human review sample of accepted labels |
