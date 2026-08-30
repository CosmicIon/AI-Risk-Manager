# Fraud Detection Simulation Studio

The AI Risk Manager platform includes a fully featured **Transaction & Fraud Simulator**, faithfully adapted from the [Fraud Detection Handbook (Chapter 3: Simulated Dataset)](https://fraud-detection-handbook.github.io/fraud-detection-handbook/Chapter_3_GettingStarted/SimulatedDataset.html).

This simulator is used to generate synthetic, rigorously modeled datasets for training and evaluating our ML models, as well as providing an interactive visual studio for Risk Analysts to observe fraud patterns in real-time.

## Mathematical Ground Truth

The simulation engine is built using highly optimized, vectorized NumPy and Pandas operations, adapting the Handbook's algorithms to an Indian BFSI context (₹ amounts, MCC codes, device IDs, and payment channels).

### 1. Profiles Generation
- **Customer Profiles**: Generated with spatial coordinates $(x,y) \sim U(0,100)^2$. Each customer is assigned a mean transaction amount $\sim U(100,5000)$ ₹ and a daily transaction frequency following a Poisson distribution.
- **Terminal Profiles**: Generated with spatial coordinates $(x,y) \sim U(0,100)^2$. Terminals are assigned a Merchant Category Code (MCC) based on weighted probabilities (e.g., Grocery, Electronics, Apparel, Dining, Money Transfer).

### 2. Spatial Association
To avoid the computationally expensive $O(N^2)$ brute-force distance calculation when mapping 20,000 customers to 2,000 terminals, the engine utilizes `scipy.spatial.cKDTree`. This provides $O(N \log N)$ spatial queries to assign each customer a list of available terminals within a configurable radius $r$.

### 3. Transaction Generation
For each customer, across $D$ days:
- Daily transactions are drawn from $K \sim \text{Poisson}(\lambda)$.
- Transaction times are assigned with a diurnal bias (peak hours between 10:00–22:00 IST).
- Transaction amounts are drawn from a Normal distribution $N(\mu, \sigma^2)$ and clipped at $\ge$ ₹10.
- The terminal is chosen uniformly from the customer's spatially associated terminal list.

## Fraud Scenario Injection

The simulator injects three canonical fraud scenarios, creating realistic, challenging datasets for ML models to detect.

### Scenario 1: High-Amount Point Fraud
- **Logic**: Any transaction exceeding a strict high-amount threshold (e.g., ₹22,000) is automatically flagged as fraud.
- **Simulation**: Models simplistic, opportunistic fraud attempts.

### Scenario 2: Compromised Terminals (POS Skimming)
- **Logic**: Each day, a fixed number of terminals are "compromised". For a window of 14 days, **100%** of transactions occurring at these terminals are flagged as fraud.
- **Simulation**: Models physical point-of-sale skimming devices capturing card details and subsequently draining accounts.

### Scenario 3: Compromised Customers (Account Takeover)
- **Logic**: Each day, a fixed number of customers are "compromised". For a window of 14 days, approximately **33%** of their transactions are selected at random, and their transaction amounts are multiplied by **$5\times$**, flagged as fraud.
- **Simulation**: Models digital account takeovers where fraudsters sporadically siphon large amounts of money while blending in with the customer's organic activity.

## Architecture & Integration

### FastAPI Backend
- **Thread Pooling**: The heavy CPU-bound Pandas generation logic is offloaded to a thread pool via `asyncio.get_event_loop().run_in_executor()` to prevent blocking the asynchronous web server.
- **WebSockets**: Live streaming of transactions at a configurable TPS (Transactions Per Second) rate, complete with mock ML risk scoring to drive the frontend UI.

### Next.js Dashboard
- **HTML5 Canvas**: Renders a live 100x100km spatial grid, depicting customers and terminals. Compromised entities are highlighted with pulsating CSS radar animations.
- **Live Ticker**: A WebSocket-connected data table that renders incoming transactions in real-time.
- **Analytics**: Calculates live Precision, Recall, F1 Score, and ₹ Cost estimations for False Positives vs. False Negatives.

## CLI Usage
To generate datasets via the terminal for CI/CD or background processing:
```bash
cd backend
python scripts/generate_synthetic_data.py --customers 10000 --terminals 1000 --days 120
```
This generates `transactions.parquet`, `returns.parquet`, and `chargebacks.parquet` with 80/20 train/holdout splits in `backend/data/synthetic`.
