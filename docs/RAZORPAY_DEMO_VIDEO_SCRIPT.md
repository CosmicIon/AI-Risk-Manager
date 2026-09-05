# 🏆 Razorpay Buildathon: 5-Minute Winning Demo Video Script

This guide gives you a **complete, word-for-word, 5-minute video presentation plan** specifically tailored to win over judges at the **Razorpay Buildathon** (`https://razorpay.com/buildathon/`).

---

## 🎯 The Secret to Winning Razorpay Judges

Razorpay is India's leading payment gateway. Their engineering leaders care deeply about:
1. **Checkout Conversion vs. Fraud:** Every extra friction step causes buyers to abandon their carts. But if you don't screen transactions, chargeback fees destroy merchant margins.
2. **Ultra-Low Latency:** In payments, an API call taking over 50ms feels broken. Sub-20ms is world-class.
3. **Smart Triage (Not Just "Yes/No"):** Auto-declining is bad. In India, 2-factor authentication (SMS/WhatsApp OTP / 3DS) is standard. Challenging medium-risk orders recovers sales.
4. **Rigor & Zero Cheating:** Most student projects make rookie mistakes like data leakage or random K-fold splits. Proving temporal integrity (7-day embargo buffer) blows judges away.

---

## 🎬 Pre-Recording Checklist (Do This Before Hitting Record!)

### 1. Browser Windows & Tabs to Prepare
Have these tabs open and zoomed cleanly (100% or 110%):
- **Tab 1:** Streamlit Dashboard at [`http://localhost:8501`](http://localhost:8501) (Already running!)
- **Tab 2:** FastAPI Swagger UI at [`http://localhost:8000/docs`](http://localhost:8000/docs) (Run `python -m src.api` in a terminal)
- **Tab 3:** [`reports/drift_report.md`](file:///d:/CODING/github/AI-Risk-Manager/reports/drift_report.md) or Architecture Diagram in VS Code.

### 2. Recording Tool
- Use **Loom**, **OBS Studio**, or **Windows Game Bar** (`Win + G`).
- Keep your camera bubble in the top-right corner if possible (adds trust and personality!).
- Speak clearly and at a confident, relaxed pace.

---

## ⏱️ 5-Minute Master Video Timeline

```
0:00 - 0:40 (40s)  ──>  The Hook & Indian FinTech Problem (Why Razorpay merchants bleed margins)
0:40 - 1:30 (50s)  ──>  Our Solution: 3-Tier Enterprise Risk Triage
1:30 - 3:00 (90s)  ──>  LIVE DEMO PART 1: Streamlit Executive Dashboard & Threshold Simulator
3:00 - 3:55 (55s)  ──>  LIVE DEMO PART 2: Real-Time FastAPI Scoring (<15ms) + Reason Codes
3:55 - 4:35 (40s)  ──>  Engineering Moat: Zero-Leakage 7-Day Embargo & Drift Monitoring
4:35 - 5:00 (25s)  ──>  Closing Pitch & Vision for Razorpay Integration
```

---

## 🎙️ Word-for-Word Spoken Script

---

### Segment 1: The Hook & Problem (0:00 – 0:40)
* **On Screen:** Start with you on camera, or show the title slide / Streamlit header: **"AI Risk Manager: Stop Merchant Margin Loss."**

> *(Spoken with energy)*:  
> "Hi everyone! Welcome to our demonstration for the Razorpay Buildathon.  
> 
> Across Indian e-commerce and digital payments, merchants are fighting a silent battle. On one side, AI-powered card fraud and automated bot attacks are causing massive chargeback losses. On the other side, crude fraud filters block honest customers, killing checkout conversion rates.  
> 
> In traditional systems, you either **block everything** and lose millions in real sales, or **allow everything** and lose margins to fraud.  
> 
> Today, we built the **AI Risk Manager**—a production-grade, sub-15-millisecond fraud mitigation platform that stops chargeback losses while keeping checkout 100% friction-free for honest customers."

---

### Segment 2: The Solution Architecture (0:40 – 1:30)
* **On Screen:** Switch to the architecture diagram or the top overview banner in Streamlit.

> *(Spoken)*:  
> "Instead of naive binary Flag-or-Clear rules, ou  r platform introduces an enterprise **3-Tier Risk Triage Policy**:  
> 
> 1. **Green Tier (Low Risk, below 0.30 score):** Instant, one-click frictionless checkout. 99.4% of honest transactions sail right through.  
> 2. **Yellow Tier (Medium Risk, between 0.30 and our optimal 0.78 cutoff):** We **CHALLENGE** the user with an instant SMS or WhatsApp OTP. Honest cardholders verify in 5 seconds and complete their purchase, while fraudsters holding stolen card numbers are stopped dead. This recovers significant revenue that other systems throw away!  
> 3. **Red Tier (High Risk, above 0.78):** Immediate automated decline or high-priority manual review.  
> 
> Let's see this running live in action!"

---

### Segment 3: Live Demo Part 1 — The Executive Dashboard (1:30 – 3:00)
* **On Screen:** Open [`http://localhost:8501`](http://localhost:8501).

> *(Spoken)*:  
> "Here is our live Executive Dashboard.  
> 
> Look at the headline verdict: on over 500,000 held-out test transactions, our system **intercepts over 97% of fraud volume**, while clearing **99.4% of legitimate volume** without any manual friction.  
> 
> In real money, this saves merchants over **$491,000**—a **74% total reduction in fraud costs**.  
> 
> *(Now scroll to the Decision Matrix)*:  
> Rather than relying on confusing statistical jargon, our dashboard gives risk executives a clear 2-by-2 decision breakdown showing true financial impacts.  
> 
> *(Now scroll to the Flagged Transaction Feed)*:  
> When an order is flagged, our **Plain-English Explainability Engine** translates complex machine learning numbers into instant human sentences. Look at this card: it tells the investigator:  
> - *'Amount is 5.2 times higher than the customer's 30-day baseline.'*  
> - *'Transaction tapped 120 miles away from customer's home anchor.'*  
> - *'Transaction occurred during high-risk overnight hours.'*  
> 
> *(Now move the interactive threshold slider)*:  
> And here is the favorite tool of every risk officer: our **Live 60-FPS Threshold Simulator**. As we adjust our sensitivity or modify unit review costs in the sidebar, the system recalculates business ROI, false-alarm costs, and savings dynamically in real time."

---

### Segment 4: Live Demo Part 2 — Real-Time FastAPI Scoring (3:00 – 3:55)
* **On Screen:** Switch to the browser tab with FastAPI Swagger docs at [`http://localhost:8000/docs`](http://localhost:8000/docs).

> *(Spoken)*:  
> "Now let's look at the engineering under the hood. In payment gateways like Razorpay, models cannot afford to run in seconds—they must answer in milliseconds.  
> 
> We built a production-ready **FastAPI microservice** with `/health`, `/metrics`, and `/v1/risk/evaluate`.  
> 
> *(Click 'POST /v1/risk/evaluate' -> 'Try it out' -> 'Execute')*:  
> Let's submit a live transaction.  
> Look at the response time: **under 15 milliseconds!**  
> In less than 15 milliseconds, our in-memory feature store calculated rolling 15-minute velocity, spatial distance, and model scores, returning:  
> - A calibrated Risk Score of `0.88`,  
> - The 3-tier action: `DECLINE`,  
> - And automated reason codes ready to be logged or passed back to the merchant checkout."

---

### Segment 5: The Engineering Moat (3:55 – 4:35)
* **On Screen:** Briefly show VS Code with [`src/split.py`](file:///d:/CODING/github/AI-Risk-Manager/src/split.py) or [`reports/drift_report.md`](file:///d:/CODING/github/AI-Risk-Manager/reports/drift_report.md).

> *(Spoken)*:  
> "What truly separates this project from ordinary machine learning demos is our strict production integrity:  
> 
> First, **Zero Lookahead Leakage**: In banking, chargebacks take about 7 days to report. Many ML models cheat by using today's chargebacks to predict today's fraud. We enforce a strict **7-day delayed feedback loop** and a **7-day purged embargo buffer** between training and test sets.  
> 
> Second, **Continuous Drift Monitoring**: Using our `drift.py` module, we track the **Population Stability Index (PSI)** across all 21 features. If customer spending shifts or fraudsters change tactics, the system automatically flags an alert before model accuracy degrades."

---

### Segment 6: The Winning Closing Pitch (4:35 – 5:00)
* **On Screen:** Bring your face/camera back full screen or show the GitHub repository / Razorpay summary slide.

> *(Spoken with a confident smile)*:  
> "To summarize: AI Risk Manager delivers:  
> - **Proven ROI**: 74% fraud cost reduction.  
> - **Enterprise Architecture**: Sub-15ms real-time scoring and 3-tier OTP triage.  
> - **Regulatory Compliance**: Defense-only, human-interpretable explanations.  
> 
> This is a drop-in ready intelligence layer that can integrate directly into payment gateways like Razorpay to protect merchants, save margins, and eliminate checkout drop-offs.  
> 
> Thank you so much, and we look forward to building this with Razorpay!"

---

## 💡 Quick Tips for Delivery

| Do's ✅ | Don'ts ❌ |
| :--- | :--- |
| **Do sound enthusiastic and confident.** You built a real, working system! | **Don't read like a robot.** Practice 2 times beforehand. |
| **Do emphasize the business dollar value ($491K saved).** Razorpay loves ROI. | **Don't drown the judge in raw math formulas.** Keep it practical. |
| **Do highlight the 3-Tier OTP Triage.** Indian judges love 2FA/OTP context. | **Don't show code scrolling endlessly.** Show working interfaces (UI & API). |
| **Do show the sub-15ms response time.** Speed is king in fintech. | **Don't exceed 5 minutes.** Keep it strictly between 4:45 and 4:58. |

---

## 🚀 How to Run Everything for Your Recording

Run these two commands in separate terminal windows:

### Terminal 1 (Dashboard):
```powershell
streamlit run src/dashboard.py
```
*(Opens at `http://localhost:8501`)*

### Terminal 2 (FastAPI Microservice):
```powershell
python -m src.api
```
*(Opens interactive API documentation at `http://localhost:8000/docs`)*
