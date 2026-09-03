import pandas as pd
import numpy as np
from src.utils import get_project_root, load_config
import time

def get_customer_spending_behaviours_features(customer_transactions, windows_size_in_days=[1,7,30]):
    # Let's sort the data by customer and then datetime
    customer_transactions = customer_transactions.sort_values('TX_DATETIME')
    
    # We create a copy of the dataframe
    customer_transactions = customer_transactions.reset_index(drop=True)
    
    # For each window size
    for window_size in windows_size_in_days:
        # Sum the amount and count the number of transactions in the window
        SUM_AMOUNT_TX_WINDOW = customer_transactions.rolling(f'{window_size}d', on='TX_DATETIME')['TX_AMOUNT'].sum()
        NB_TX_WINDOW = customer_transactions.rolling(f'{window_size}d', on='TX_DATETIME')['TX_AMOUNT'].count()
        
        # Calculate the average amount
        AVG_AMOUNT_TX_WINDOW = SUM_AMOUNT_TX_WINDOW / NB_TX_WINDOW
        
        # We save these features in the dataframe
        customer_transactions[f'CUSTOMER_ID_NB_TX_{window_size}DAY_WINDOW'] = list(NB_TX_WINDOW)
        customer_transactions[f'CUSTOMER_ID_AVG_AMOUNT_{window_size}DAY_WINDOW'] = list(AVG_AMOUNT_TX_WINDOW)
        
    return customer_transactions

def get_count_risk_rolling_window(terminal_transactions, delay_period=7, windows_size_in_days=[1,7,30]):
    terminal_transactions = terminal_transactions.sort_values('TX_DATETIME')
    terminal_transactions = terminal_transactions.reset_index(drop=True)
    
    for window_size in windows_size_in_days:
        # Shift the series by delay_period
        # Since we are using time-based rolling on the entire history up to the transaction,
        # to strictly avoid leakage we must compute the stats over [t - delay - window, t - delay].
        # A simpler approach used in the handbook:
        # 1. Compute rolling sum of frauds and count of tx up to t-delay
        
        # Create a delayed datetime column
        delayed_datetime = terminal_transactions['TX_DATETIME'] - pd.Timedelta(days=delay_period)
        
        # To compute the number of frauds in [t - delay - window, t - delay], 
        # we can compute the cumulative sum of frauds up to t-delay and subtract the cumulative sum up to t-delay-window.
        
        # A more straightforward way:
        # Create a series with TX_DATETIME as index
        fraud_ts = pd.Series(terminal_transactions['TX_FRAUD'].values, index=terminal_transactions['TX_DATETIME'])
        
        # Compute rolling stats for the window size
        rolling_fraud_sum = fraud_ts.rolling(f'{window_size}d').sum()
        rolling_tx_count = fraud_ts.rolling(f'{window_size}d').count()
        
        # Now, we need the values of these rolling stats at t - delay.
        # We can reindex or use asof/merge_asof.
        # merge_asof is efficient.
        
        stats_df = pd.DataFrame({
            'TX_DATETIME': fraud_ts.index,
            f'TERMINAL_ID_NB_FRAUD_{window_size}DAY_WINDOW': rolling_fraud_sum.values,
            f'TERMINAL_ID_NB_TX_{window_size}DAY_WINDOW': rolling_tx_count.values
        })
        
        terminal_transactions['DELAYED_DATETIME'] = terminal_transactions['TX_DATETIME'] - pd.Timedelta(days=delay_period)
        
        # We merge the stats back. For a transaction at t, we look up the stats at t - delay.
        merged = pd.merge_asof(
            terminal_transactions.sort_values('DELAYED_DATETIME'),
            stats_df.sort_values('TX_DATETIME'),
            left_on='DELAYED_DATETIME',
            right_on='TX_DATETIME',
            direction='backward',
            suffixes=('', '_stats')
        )
        
        # Fill NaNs with 0 (for the first few days before delay period)
        merged[f'TERMINAL_ID_NB_FRAUD_{window_size}DAY_WINDOW'] = merged[f'TERMINAL_ID_NB_FRAUD_{window_size}DAY_WINDOW'].fillna(0)
        merged[f'TERMINAL_ID_NB_TX_{window_size}DAY_WINDOW'] = merged[f'TERMINAL_ID_NB_TX_{window_size}DAY_WINDOW'].fillna(0)
        
        # Compute risk score
        # Risk score = (nb frauds + 1) / (nb tx + 10) # Laplace smoothing as per handbook to avoid 0/0 and 1/1 noise
        risk_score = merged[f'TERMINAL_ID_NB_FRAUD_{window_size}DAY_WINDOW'] / (merged[f'TERMINAL_ID_NB_TX_{window_size}DAY_WINDOW'] + 0.0001)
        
        terminal_transactions[f'TERMINAL_ID_NB_TX_{window_size}DAY_WINDOW'] = merged[f'TERMINAL_ID_NB_TX_{window_size}DAY_WINDOW'].values
        terminal_transactions[f'TERMINAL_ID_RISK_{window_size}DAY_WINDOW'] = risk_score.values
        terminal_transactions.drop(columns=['DELAYED_DATETIME'], inplace=True)
        
    return terminal_transactions


def main():
    print("Running Feature Engineering...")
    config = load_config()
    feat_cfg = config['features']
    
    root = get_project_root()
    raw_dir = root / 'data' / 'raw'
    proc_dir = root / 'data' / 'processed'
    proc_dir.mkdir(parents=True, exist_ok=True)
    
    print("Loading raw transactions...")
    transactions = pd.read_pickle(raw_dir / 'transactions.pkl')
    
    print("Computing date/time features...")
    transactions['TX_DURING_WEEKEND'] = transactions['TX_DATETIME'].dt.weekday >= 5
    transactions['TX_DURING_WEEKEND'] = transactions['TX_DURING_WEEKEND'].astype(int)
    transactions['TX_DURING_NIGHT'] = (transactions['TX_DATETIME'].dt.hour < 6).astype(int)
    
    print("Computing customer-level features...")
    start_time = time.time()
    transactions = transactions.groupby('CUSTOMER_ID').apply(
        lambda x: get_customer_spending_behaviours_features(x, feat_cfg['customer_windows']),
        include_groups=False
    )
    # The apply creates a multi-index, we drop it
    transactions = transactions.reset_index(level=0)
    transactions = transactions.sort_values('TX_DATETIME').reset_index(drop=True)
    print(f"Customer features computed in {time.time() - start_time:.2f}s")
    
    print("Computing amount deviation features (z-score)...")
    # For z-score we use the 30-day window
    transactions['TX_AMOUNT_ZSCORE'] = (transactions['TX_AMOUNT'] - transactions['CUSTOMER_ID_AVG_AMOUNT_30DAY_WINDOW']) / (transactions.rolling('30d', on='TX_DATETIME')['TX_AMOUNT'].std().fillna(1.0) + 0.001)
    
    print("Computing terminal-level features...")
    start_time = time.time()
    transactions = transactions.groupby('TERMINAL_ID').apply(
        lambda x: get_count_risk_rolling_window(x, delay_period=feat_cfg['delay_period'], windows_size_in_days=feat_cfg['terminal_windows']),
        include_groups=False
    )
    transactions = transactions.reset_index(level=0)
    transactions = transactions.sort_values('TX_DATETIME').reset_index(drop=True)
    print(f"Terminal features computed in {time.time() - start_time:.2f}s")
    
    print("Dropping warm-up period...")
    # The first 'delay_period' + max window size days will not have full history.
    # In the handbook, they drop the first 21 days or so. We'll drop the first 30 days (max window size).
    start_date = transactions['TX_DATETIME'].min()
    valid_start_date = start_date + pd.Timedelta(days=max(feat_cfg['customer_windows'] + feat_cfg['terminal_windows']))
    
    print(f"Original shape: {transactions.shape}")
    transactions = transactions[transactions['TX_DATETIME'] >= valid_start_date]
    print(f"Shape after warm-up drop: {transactions.shape}")
    
    print("Saving engineered features...")
    transactions.to_parquet(proc_dir / 'features.parquet')
    
    print("Feature engineering complete!")

if __name__ == "__main__":
    main()
