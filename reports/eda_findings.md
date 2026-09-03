# Exploratory Data Analysis Findings

## Overall Statistics
- **Total Transactions:** 3,608,858
- **Date Range:** 2018-04-01 to 2018-09-27
- **Customers:** 10,000
- **Terminals:** 20,000

## Fraud Summary
- **Overall Fraud Rate:** 0.44% (15,958 fraudulent transactions)

The dataset contains very rare fraud, which is typical for card-not-present transactions. This extreme class imbalance requires special handling during model training (e.g., sample weighting) and means that naive accuracy is a meaningless metric.

### Fraud by Scenario
1. **Scenario 1 (High Amount):** 2,005 transactions. These are simple heuristic catches (amounts > $220).
2. **Scenario 2 (Compromised Terminals):** 9,206 transactions. This simulates skimming or phishing at specific terminals.
3. **Scenario 3 (Compromised Customers):** 4,747 transactions. This simulates card-not-present credential theft where fraudsters multiply normal spending by 5x.

## Patterns Observed
- **Time of Day:** Transaction volume dips overnight and peaks during the day.
- **Amounts:** Fraudulent transactions tend to have higher amounts on average (driven by Scenarios 1 and 3), but there is significant overlap with legitimate transaction amounts.

*(See the `figures/` directory for detailed charts).*
