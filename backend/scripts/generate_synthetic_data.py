import os
import uuid
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_data():
    np.random.seed(42)
    
    output_dir = "data/synthetic"
    holdout_dir = os.path.join(output_dir, "holdout")
    os.makedirs(holdout_dir, exist_ok=True)
    
    print("Generating 100,000 transactions...")
    
    num_txns = 100000
    customer_ids = [f"cust_{i}" for i in range(1, 10001)]
    merchants = [f"merch_{i}" for i in range(1, 501)]
    categories = ['electronics', 'fashion', 'groceries', 'other']
    cat_probs = [0.20, 0.30, 0.25, 0.25]
    
    # Dates: last 180 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    # Lognormal amounts (mean approx 2500)
    # log(2500) approx 7.82. Let's use mean=7.5, sigma=0.8
    amounts = np.random.lognormal(mean=7.5, sigma=0.8, size=num_txns)
    amounts = np.clip(amounts, 10, 500000).round(2)
    
    # Non-uniform timestamps (bias 10am-10pm)
    def random_date_biased(start, end, n):
        dates = []
        for _ in range(n):
            dt = start + timedelta(seconds=np.random.randint(0, int((end - start).total_seconds())))
            # bias towards 10am-10pm
            if 10 <= dt.hour <= 22 or np.random.random() < 0.2:
                dates.append(dt)
            else:
                # retry
                dt = dt.replace(hour=np.random.randint(10, 23))
                dates.append(dt)
        return dates

    timestamps = random_date_biased(start_date, end_date, num_txns)
    timestamps.sort() # sort by time
    
    txns = pd.DataFrame({
        "transaction_id": [f"tx_{uuid.uuid4().hex[:8]}" for _ in range(num_txns)],
        "customer_id": np.random.choice(customer_ids, num_txns),
        "merchant_id": np.random.choice(merchants, num_txns),
        "category": np.random.choice(categories, num_txns, p=cat_probs),
        "amount": amounts,
        "timestamp": timestamps,
        "device_fingerprint": [f"device_{np.random.randint(1, 10000)}" for _ in range(num_txns)]
    })
    
    print("Generating 5,000 return requests...")
    num_returns = 5000
    
    # Select transactions to return
    return_txns = txns.sample(num_returns, replace=False)
    
    # Abuse logic (5% = 250 requests)
    abuse_indices = np.random.choice(return_txns.index, int(num_returns * 0.05), replace=False)
    
    is_abusive = np.zeros(num_returns, dtype=bool)
    is_abusive[np.where(return_txns.index.isin(abuse_indices))[0]] = True
    
    return_amounts = return_txns['amount'] * np.where(is_abusive, 1.0, np.random.uniform(0.1, 1.0, num_returns))
    return_amounts = return_amounts.round(2)
    
    # Assign some patterns to abusive
    device_fingerprints = return_txns['device_fingerprint'].values
    for i in range(num_returns):
        if is_abusive[i]:
            if np.random.random() < 0.8:
                device_fingerprints[i] = "device_mismatch_" + str(np.random.randint(1, 1000))
    
    returns = pd.DataFrame({
        "request_id": [f"ret_{uuid.uuid4().hex[:8]}" for _ in range(num_returns)],
        "transaction_id": return_txns['transaction_id'].values,
        "customer_id": return_txns['customer_id'].values,
        "order_amount": return_txns['amount'].values,
        "return_amount": return_amounts.values,
        "category": return_txns['category'].values,
        "order_date": return_txns['timestamp'].values,
        "return_date": return_txns['timestamp'].values + pd.to_timedelta(np.random.randint(1, 30, num_returns), unit='D'),
        "device_fingerprint": device_fingerprints,
        "is_abusive": is_abusive
    })
    
    # Sort returns by date
    returns = returns.sort_values("return_date").reset_index(drop=True)
    
    print("Generating 500 chargeback cases...")
    num_chargebacks = 500
    cb_txns = txns[~txns['transaction_id'].isin(returns['transaction_id'])].sample(num_chargebacks, replace=False)
    
    outcomes = np.random.choice(["WON", "LOST", "PENDING"], num_chargebacks, p=[0.4, 0.5, 0.1])
    reason_codes = np.random.choice(["10.4", "13.1", "13.3", "12.2"], num_chargebacks)
    
    chargebacks = pd.DataFrame({
        "case_id": [f"cb_{uuid.uuid4().hex[:8]}" for _ in range(num_chargebacks)],
        "transaction_id": cb_txns['transaction_id'].values,
        "amount": cb_txns['amount'].values,
        "reason_code": reason_codes,
        "outcome": outcomes,
        "created_at": cb_txns['timestamp'].values + pd.to_timedelta(np.random.randint(10, 60, num_chargebacks), unit='D')
    })
    chargebacks = chargebacks.sort_values("created_at").reset_index(drop=True)
    
    # Train/test split by time (80/20)
    def split_and_save(df, time_col, name):
        split_idx = int(len(df) * 0.8)
        train = df.iloc[:split_idx]
        holdout = df.iloc[split_idx:]
        
        train.to_parquet(os.path.join(output_dir, f"{name}.parquet"), index=False)
        holdout.to_parquet(os.path.join(holdout_dir, f"{name}.parquet"), index=False)
        print(f"Saved {name}: Train {len(train)}, Holdout {len(holdout)}")

    split_and_save(txns, "timestamp", "transactions")
    split_and_save(returns, "return_date", "returns")
    split_and_save(chargebacks, "created_at", "chargebacks")
    
    print("Synthetic data generation complete.")

if __name__ == "__main__":
    generate_data()
