import pytest
import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from datetime import datetime, timedelta
from src.features import get_customer_spending_behaviours_features, get_count_risk_rolling_window

def test_customer_zscore_is_customer_specific():
    # Customer with identical transactions: std should be 0, Z-score should be 0
    base_time = pd.Timestamp('2026-01-01 10:00:00')
    txs = pd.DataFrame({
        'CUSTOMER_ID': [1, 1, 1, 1],
        'TX_DATETIME': [base_time + pd.Timedelta(days=i) for i in range(4)],
        'TX_AMOUNT': [50.0, 50.0, 50.0, 50.0]
    })
    
    res = get_customer_spending_behaviours_features(txs, windows_size_in_days=[1, 7, 30])
    
    assert 'CUSTOMER_ID_STD_AMOUNT_30DAY_WINDOW' in res.columns
    assert 'TX_AMOUNT_ZSCORE' in res.columns
    # With identical spending, amount - avg = 0, so Z-score is 0.0
    assert np.allclose(res['TX_AMOUNT_ZSCORE'].values, 0.0)

def test_sub_hour_burst_and_velocity_features():
    base_time = pd.Timestamp('2026-01-01 12:00:00')
    txs = pd.DataFrame({
        'CUSTOMER_ID': [1, 1, 1],
        # 3 transactions: at 12:00, 12:05 (300s later), and 12:10 (300s later)
        'TX_DATETIME': [
            base_time, 
            base_time + pd.Timedelta(minutes=5), 
            base_time + pd.Timedelta(minutes=10)
        ],
        'TX_AMOUNT': [20.0, 25.0, 30.0]
    })
    
    res = get_customer_spending_behaviours_features(txs, windows_size_in_days=[1, 7, 30])
    
    # In 15 minutes window, all 3 should be counted on the 3rd transaction
    assert res['CUSTOMER_ID_NB_TX_15MIN_WINDOW'].iloc[-1] == 3
    assert res['CUSTOMER_ID_NB_TX_1HOUR_WINDOW'].iloc[-1] == 3
    # Time since last tx for 2nd and 3rd transaction should be 300 seconds
    assert res['TIME_SINCE_LAST_TX'].iloc[1] == 300.0
    assert res['TIME_SINCE_LAST_TX'].iloc[2] == 300.0

def test_spatial_distance_calculation():
    # Verify Euclidean distance calculation
    # (0, 0) to (3, 4) should be 5.0
    x_cust, y_cust = 0.0, 0.0
    x_term, y_term = 3.0, 4.0
    dist = np.sqrt((x_cust - x_term)**2 + (y_cust - y_term)**2)
    assert dist == 5.0

def test_terminal_risk_delay_no_future_leakage():
    # Transaction on day 10 with delay 7 days must only see events up to day 3
    base_time = pd.Timestamp('2026-01-01 10:00:00')
    txs = pd.DataFrame({
        'TERMINAL_ID': [100, 100],
        'TX_DATETIME': [base_time, base_time + pd.Timedelta(days=5)], # Day 0 and Day 5
        'TX_FRAUD': [1, 1] # Fraud occurred at day 0 and day 5
    })
    
    res = get_count_risk_rolling_window(txs, delay_period=7, windows_size_in_days=[7])
    
    # At Day 5, looking back 7 days means looking at Day -2.
    # So fraud at Day 0 should NOT be known at Day 5 (because 5 - 7 = -2, which is before Day 0)!
    # Hence risk score and tx count must be 0
    assert res['TERMINAL_ID_RISK_7DAY_WINDOW'].iloc[1] == 0
    assert res['TERMINAL_ID_NB_TX_7DAY_WINDOW'].iloc[1] == 0
