import pandas as pd
import numpy as np
from src.utils import get_project_root, load_config
import time

def get_customer_spending_behaviours_features(customer_transactions, windows_size_in_days=[1,7,30]):
    # Let's sort the data by customer and then datetime
    customer_transactions = customer_transactions.sort_values('TX_DATETIME')
    customer_transactions = customer_transactions.reset_index(drop=True)
    
    # 1. Sub-hour burst & velocity features
    # 15 minutes rolling count
    customer_transactions['CUSTOMER_ID_NB_TX_15MIN_WINDOW'] = list(
        customer_transactions.rolling('15min', on='TX_DATETIME')['TX_AMOUNT'].count()
    )
    # 1 hour rolling count
    customer_transactions['CUSTOMER_ID_NB_TX_1HOUR_WINDOW'] = list(
        customer_transactions.rolling('1h', on='TX_DATETIME')['TX_AMOUNT'].count()
    )
    # Time elapsed in seconds since previous transaction
    time_diff = customer_transactions['TX_DATETIME'].diff().dt.total_seconds().fillna(86400.0)
    customer_transactions['TIME_SINCE_LAST_TX'] = time_diff.values
    
    # 2. Daily and multi-day rolling windows
    for window_size in windows_size_in_days:
        SUM_AMOUNT_TX_WINDOW = customer_transactions.rolling(f'{window_size}D', on='TX_DATETIME')['TX_AMOUNT'].sum()
        NB_TX_WINDOW = customer_transactions.rolling(f'{window_size}D', on='TX_DATETIME')['TX_AMOUNT'].count()
        AVG_AMOUNT_TX_WINDOW = SUM_AMOUNT_TX_WINDOW / NB_TX_WINDOW
        
        customer_transactions[f'CUSTOMER_ID_NB_TX_{window_size}DAY_WINDOW'] = list(NB_TX_WINDOW)
        customer_transactions[f'CUSTOMER_ID_AVG_AMOUNT_{window_size}DAY_WINDOW'] = list(AVG_AMOUNT_TX_WINDOW)
        
    # 3. Customer-specific 30-day standard deviation & corrected Z-Score
    std_30d = customer_transactions.rolling('30D', on='TX_DATETIME')['TX_AMOUNT'].std().fillna(0.0)
    customer_transactions['CUSTOMER_ID_STD_AMOUNT_30DAY_WINDOW'] = list(std_30d)
    customer_transactions['TX_AMOUNT_ZSCORE'] = (
        customer_transactions['TX_AMOUNT'] - customer_transactions['CUSTOMER_ID_AVG_AMOUNT_30DAY_WINDOW']
    ) / (customer_transactions['CUSTOMER_ID_STD_AMOUNT_30DAY_WINDOW'] + 1.0)
        
    return customer_transactions

def get_count_risk_rolling_window(terminal_transactions, delay_period=7, windows_size_in_days=[1,7,30]):
    terminal_transactions = terminal_transactions.sort_values('TX_DATETIME')
    terminal_transactions = terminal_transactions.reset_index(drop=True)
    
    for window_size in windows_size_in_days:
        delayed_datetime = terminal_transactions['TX_DATETIME'] - pd.Timedelta(days=delay_period)
        
        fraud_ts = pd.Series(terminal_transactions['TX_FRAUD'].values, index=terminal_transactions['TX_DATETIME'])
        
        rolling_fraud_sum = fraud_ts.rolling(f'{window_size}D').sum()
        rolling_tx_count = fraud_ts.rolling(f'{window_size}D').count()
        
        stats_df = pd.DataFrame({
            'TX_DATETIME': fraud_ts.index,
            f'TERMINAL_ID_NB_FRAUD_{window_size}DAY_WINDOW': rolling_fraud_sum.values,
            f'TERMINAL_ID_NB_TX_{window_size}DAY_WINDOW': rolling_tx_count.values
        })
        
        terminal_transactions['DELAYED_DATETIME'] = terminal_transactions['TX_DATETIME'] - pd.Timedelta(days=delay_period)
        
        merged = pd.merge_asof(
            terminal_transactions.sort_values('DELAYED_DATETIME'),
            stats_df.sort_values('TX_DATETIME'),
            left_on='DELAYED_DATETIME',
            right_on='TX_DATETIME',
            direction='backward',
            suffixes=('', '_stats')
        )
        
        merged[f'TERMINAL_ID_NB_FRAUD_{window_size}DAY_WINDOW'] = merged[f'TERMINAL_ID_NB_FRAUD_{window_size}DAY_WINDOW'].fillna(0)
        merged[f'TERMINAL_ID_NB_TX_{window_size}DAY_WINDOW'] = merged[f'TERMINAL_ID_NB_TX_{window_size}DAY_WINDOW'].fillna(0)
        
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
    
    print("Computing customer-terminal spatial distance...")
    cust_prof_file = raw_dir / 'customer_profiles.pkl'
    term_prof_file = raw_dir / 'terminal_profiles.pkl'
    if cust_prof_file.exists() and term_prof_file.exists():
        customers = pd.read_pickle(cust_prof_file)
        terminals = pd.read_pickle(term_prof_file)
        
        merged_coords = transactions[['CUSTOMER_ID', 'TERMINAL_ID']].copy()
        merged_coords = merged_coords.merge(customers[['CUSTOMER_ID', 'x_customer_id', 'y_customer_id']], on='CUSTOMER_ID', how='left')
        merged_coords = merged_coords.merge(terminals[['TERMINAL_ID', 'x_terminal_id', 'y_terminal_id']], on='TERMINAL_ID', how='left')
        
        dist = np.sqrt(
            (merged_coords['x_customer_id'] - merged_coords['x_terminal_id'])**2 + 
            (merged_coords['y_customer_id'] - merged_coords['y_terminal_id'])**2
        )
        transactions['TX_DIST_CUSTOMER_TERMINAL'] = dist.fillna(0.0).values
    else:
        transactions['TX_DIST_CUSTOMER_TERMINAL'] = 0.0
        
    print("Computing customer-level features (rolling windows, burst, and customer Z-score)...")
    start_time = time.time()
    transactions = transactions.groupby('CUSTOMER_ID').apply(
        lambda x: get_customer_spending_behaviours_features(x, feat_cfg['customer_windows']),
        include_groups=False
    )
    transactions = transactions.reset_index(level=0)
    transactions = transactions.sort_values('TX_DATETIME').reset_index(drop=True)
    print(f"Customer features computed in {time.time() - start_time:.2f}s")
    
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
