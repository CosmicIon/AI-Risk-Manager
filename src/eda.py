import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from src.utils import get_project_root
import os

def main():
    print("Running Exploratory Data Analysis (EDA)...")
    root = get_project_root()
    raw_dir = root / 'data' / 'raw'
    reports_dir = root / 'reports'
    figures_dir = reports_dir / 'figures'
    
    figures_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    print("Loading data...")
    transactions = pd.read_pickle(raw_dir / 'transactions.pkl')
    customers = pd.read_pickle(raw_dir / 'customer_profiles.pkl')
    terminals = pd.read_pickle(raw_dir / 'terminal_profiles.pkl')
    
    # 1. Overall stats
    total_tx = len(transactions)
    n_cust = len(customers)
    n_term = len(terminals)
    start_dt = transactions['TX_DATETIME'].min()
    end_dt = transactions['TX_DATETIME'].max()
    
    # 2. Fraud stats
    frauds = transactions[transactions['TX_FRAUD'] == 1]
    n_frauds = len(frauds)
    fraud_rate = n_frauds / total_tx * 100
    
    scenario_counts = frauds['TX_FRAUD_SCENARIO'].value_counts().sort_index()
    
    # 3. Time patterns
    transactions['TX_DATE'] = transactions['TX_DATETIME'].dt.date
    daily_fraud = transactions.groupby('TX_DATE').apply(lambda x: x['TX_FRAUD'].mean() * 100, include_groups=False)
    
    plt.figure(figsize=(10,5))
    daily_fraud.plot()
    plt.title('Daily Fraud Rate (%)')
    plt.xlabel('Date')
    plt.ylabel('Fraud Rate (%)')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(figures_dir / 'fraud_rate_by_day.png')
    plt.close()
    
    transactions['TX_HOUR'] = transactions['TX_DATETIME'].dt.hour
    hourly_volume = transactions['TX_HOUR'].value_counts().sort_index()
    
    plt.figure(figsize=(10,5))
    sns.barplot(x=hourly_volume.index, y=hourly_volume.values, color='steelblue')
    plt.title('Transaction Volume by Hour of Day')
    plt.xlabel('Hour')
    plt.ylabel('Number of Transactions')
    plt.tight_layout()
    plt.savefig(figures_dir / 'transactions_per_hour.png')
    plt.close()
    
    # 4. Scenario breakdown
    plt.figure(figsize=(8,5))
    sns.barplot(x=scenario_counts.index, y=scenario_counts.values, palette='Reds')
    plt.title('Fraudulent Transactions by Scenario')
    plt.xlabel('Scenario')
    plt.ylabel('Count')
    plt.xticks([0,1,2], ['High Amount (1)', 'Compromised Terminal (2)', 'Compromised Customer (3)'])
    plt.tight_layout()
    plt.savefig(figures_dir / 'fraud_by_scenario.png')
    plt.close()
    
    # 5. Amount distribution
    plt.figure(figsize=(10,5))
    sns.histplot(data=transactions, x='TX_AMOUNT', hue='TX_FRAUD', bins=50, log_scale=(False, True), stat='count')
    plt.title('Transaction Amount Distribution (Log Scale Count)')
    plt.xlabel('Amount')
    plt.ylabel('Log(Count)')
    plt.tight_layout()
    plt.savefig(figures_dir / 'amount_distribution.png')
    plt.close()
    
    # Report generation
    report_content = f"""# Exploratory Data Analysis Findings

## Overall Statistics
- **Total Transactions:** {total_tx:,}
- **Date Range:** {start_dt.strftime('%Y-%m-%d')} to {end_dt.strftime('%Y-%m-%d')}
- **Customers:** {n_cust:,}
- **Terminals:** {n_term:,}

## Fraud Summary
- **Overall Fraud Rate:** {fraud_rate:.2f}% ({n_frauds:,} fraudulent transactions)

The dataset contains very rare fraud, which is typical for card-not-present transactions. This extreme class imbalance requires special handling during model training (e.g., sample weighting) and means that naive accuracy is a meaningless metric.

### Fraud by Scenario
1. **Scenario 1 (High Amount):** {scenario_counts.get(1, 0):,} transactions. These are simple heuristic catches (amounts > $220).
2. **Scenario 2 (Compromised Terminals):** {scenario_counts.get(2, 0):,} transactions. This simulates skimming or phishing at specific terminals.
3. **Scenario 3 (Compromised Customers):** {scenario_counts.get(3, 0):,} transactions. This simulates card-not-present credential theft where fraudsters multiply normal spending by 5x.

## Patterns Observed
- **Time of Day:** Transaction volume dips overnight and peaks during the day.
- **Amounts:** Fraudulent transactions tend to have higher amounts on average (driven by Scenarios 1 and 3), but there is significant overlap with legitimate transaction amounts.

*(See the `figures/` directory for detailed charts).*
"""
    
    with open(reports_dir / 'eda_findings.md', 'w') as f:
        f.write(report_content)
        
    print("EDA complete. Findings written to reports/eda_findings.md.")

if __name__ == "__main__":
    main()
