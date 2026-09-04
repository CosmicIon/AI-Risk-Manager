import argparse
from datetime import datetime, timedelta
import os
from pathlib import Path
import random
import time

import numpy as np
import pandas as pd

from src.adapters.kaggle import KaggleCreditCardAdapter, generate_sample_kaggle_data
from src.adapters.ieee_cis import IEEECISAdapter, generate_sample_ieee_cis_data
from src.utils import get_project_root, load_config

def generate_customer_profiles_table(n_customers, random_state=42):
    np.random.seed(random_state)
    customer_id_properties=[]
    for customer_id in range(n_customers):
        x_customer_id = np.random.uniform(0,100)
        y_customer_id = np.random.uniform(0,100)
        mean_amount = np.random.uniform(5,100)
        std_amount = mean_amount/2
        mean_nb_tx_per_day = np.random.uniform(0,4)
        customer_id_properties.append([customer_id,
                                      x_customer_id, y_customer_id,
                                      mean_amount, std_amount,
                                      mean_nb_tx_per_day])
    customer_profiles_table = pd.DataFrame(customer_id_properties, columns=['CUSTOMER_ID',
                                                                      'x_customer_id', 'y_customer_id',
                                                                      'mean_amount', 'std_amount',
                                                                      'mean_nb_tx_per_day'])
    return customer_profiles_table

def generate_terminal_profiles_table(n_terminals, random_state=42):
    np.random.seed(random_state)
    terminal_id_properties=[]
    for terminal_id in range(n_terminals):
        x_terminal_id = np.random.uniform(0,100)
        y_terminal_id = np.random.uniform(0,100)
        terminal_id_properties.append([terminal_id, x_terminal_id, y_terminal_id])
    terminal_profiles_table = pd.DataFrame(terminal_id_properties, columns=['TERMINAL_ID',
                                                                      'x_terminal_id', 'y_terminal_id'])
    return terminal_profiles_table

def compute_available_terminals_vectorized(customer_profiles_table, terminal_profiles_table, r):
    """
    Vectorized computation of customer-terminal proximity using 2D NumPy broadcasting.
    Replaces slow row-by-row apply with a single C-speed matrix distance operation.
    """
    x_y_cust = customer_profiles_table[['x_customer_id', 'y_customer_id']].values.astype(float)
    x_y_term = terminal_profiles_table[['x_terminal_id', 'y_terminal_id']].values.astype(float)
    
    # Broadcast Euclidean distance: (N_cust, 1, 2) - (1, N_term, 2) -> (N_cust, N_term)
    diff = x_y_cust[:, np.newaxis, :] - x_y_term[np.newaxis, :, :]
    dist_matrix = np.sqrt(np.sum(diff ** 2, axis=2))
    
    n_terminals = len(terminal_profiles_table)
    available = []
    for i in range(len(customer_profiles_table)):
        matches = np.where(dist_matrix[i] < r)[0].tolist()
        if len(matches) == 0:
            matches = [int(np.random.randint(0, n_terminals))]
        available.append(matches)
    return available

def generate_transactions_table_vectorized(customer_profile, start_date, nb_days):
    """
    Vectorized simulation of customer transactions using NumPy array operations.
    """
    cid = int(customer_profile.CUSTOMER_ID)
    np.random.seed(cid)
    random.seed(cid)
    
    daily_counts = np.random.poisson(customer_profile.mean_nb_tx_per_day, size=nb_days)
    total_tx = int(daily_counts.sum())
    if total_tx == 0:
        return pd.DataFrame(columns=['TX_TIME_SECONDS', 'TX_TIME_DAYS', 'CUSTOMER_ID', 'TERMINAL_ID', 'TX_AMOUNT', 'TX_DATETIME'])
    
    days_arr = np.repeat(np.arange(nb_days), daily_counts)
    
    # Seconds within day: normal(43200, 20000)
    time_tx = np.random.normal(43200, 20000, size=total_tx).astype(int)
    invalid_mask = (time_tx < 0) | (time_tx >= 86400)
    if np.any(invalid_mask):
        time_tx[invalid_mask] = np.random.uniform(0, 86400, size=int(np.sum(invalid_mask))).astype(int)
        
    time_seconds = time_tx + days_arr * 86400
    
    # Monetary amounts
    mean_amt = customer_profile.mean_amount
    std_amt = customer_profile.std_amount
    amounts = np.random.normal(mean_amt, std_amt, size=total_tx)
    neg_mask = amounts < 0
    if np.any(neg_mask):
        amounts[neg_mask] = np.random.uniform(0, mean_amt * 2, size=int(np.sum(neg_mask)))
    amounts = np.round(amounts, decimals=2)
    
    # Available terminals
    term_choices = customer_profile.available_terminals
    if len(term_choices) > 0:
        terminals = [random.choice(term_choices) for _ in range(total_tx)]
    else:
        terminals = [0] * total_tx
        
    df = pd.DataFrame({
        'TX_TIME_SECONDS': time_seconds,
        'TX_TIME_DAYS': days_arr,
        'CUSTOMER_ID': cid,
        'TERMINAL_ID': terminals,
        'TX_AMOUNT': amounts,
    })
    
    start_ts = pd.Timestamp(start_date)
    df['TX_DATETIME'] = start_ts + pd.to_timedelta(df['TX_TIME_SECONDS'], unit='s')
    return df

def generate_dataset(n_customers, n_terminals, nb_days, start_date, r, random_state=42):
    start_time = time.time()
    
    # 1. Profiles
    customer_profiles_table = generate_customer_profiles_table(n_customers, random_state)
    terminal_profiles_table = generate_terminal_profiles_table(n_terminals, random_state)
    
    # 2. Terminals associated to customers (Vectorized)
    customer_profiles_table['available_terminals'] = compute_available_terminals_vectorized(
        customer_profiles_table, terminal_profiles_table, r=r
    )
        
    # 3. Transactions (Vectorized per customer)
    tx_list = [
        generate_transactions_table_vectorized(row, start_date=start_date, nb_days=nb_days)
        for _, row in customer_profiles_table.iterrows()
    ]
    
    transactions_df = pd.concat(tx_list, ignore_index=True)
    transactions_df = transactions_df.sort_values('TX_DATETIME').reset_index(drop=True)
    transactions_df['TRANSACTION_ID'] = transactions_df.index
    
    return customer_profiles_table, terminal_profiles_table, transactions_df

def add_frauds(customer_profiles_table, terminal_profiles_table, transactions_df, nb_days, random_state=42):
    random.seed(random_state)
    np.random.seed(random_state)
    
    # Initialize labels
    transactions_df['TX_FRAUD'] = 0
    transactions_df['TX_FRAUD_SCENARIO'] = 0
    
    # Scenario 1: Amounts > 220
    transactions_df.loc[transactions_df.TX_AMOUNT > 220, 'TX_FRAUD'] = 1
    transactions_df.loc[transactions_df.TX_AMOUNT > 220, 'TX_FRAUD_SCENARIO'] = 1
    
    # Scenario 2: Compromised terminals
    for day in range(nb_days):
        compromised_terminals = terminal_profiles_table.TERMINAL_ID.sample(n=2, random_state=day)
        
        compromised_transactions = transactions_df[
            (transactions_df.TX_TIME_DAYS >= day) & 
            (transactions_df.TX_TIME_DAYS < day + 28) & 
            (transactions_df.TERMINAL_ID.isin(compromised_terminals))
        ]
        
        transactions_df.loc[compromised_transactions.index, 'TX_FRAUD'] = 1
        transactions_df.loc[compromised_transactions.index, 'TX_FRAUD_SCENARIO'] = 2
        
    # Scenario 3: Compromised customers
    for day in range(nb_days):
        compromised_customers = customer_profiles_table.CUSTOMER_ID.sample(n=3, random_state=day)
        
        compromised_transactions = transactions_df[
            (transactions_df.TX_TIME_DAYS >= day) & 
            (transactions_df.TX_TIME_DAYS < day + 14) & 
            (transactions_df.CUSTOMER_ID.isin(compromised_customers))
        ]
        
        nb_compromised_transactions = len(compromised_transactions)
        if nb_compromised_transactions > 0:
            random.seed(day)
            indices_to_compromise = random.sample(list(compromised_transactions.index), int(nb_compromised_transactions/3))
            
            transactions_df.loc[indices_to_compromise, 'TX_AMOUNT'] = transactions_df.loc[indices_to_compromise, 'TX_AMOUNT'] * 5
            transactions_df.loc[indices_to_compromise, 'TX_FRAUD'] = 1
            transactions_df.loc[indices_to_compromise, 'TX_FRAUD_SCENARIO'] = 3
            
    return transactions_df

def main():
    parser = argparse.ArgumentParser(description="Data Ingestion & Simulation Engine")
    parser.add_argument(
        "--source",
        choices=["simulator", "kaggle", "ieee_cis"],
        default=None,
        help="Data source to ingest (simulator, kaggle, or ieee_cis)",
    )
    args = parser.parse_args()

    config = load_config()
    sim_cfg = config['simulator']
    source = args.source or config.get("data_source", "simulator")

    root = get_project_root()
    raw_dir = root / 'data' / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)

    if source == "kaggle":
        print("Ingesting Kaggle Credit Card Fraud benchmark dataset...")
        raw_kaggle_path = raw_dir / "creditcard.csv"
        if raw_kaggle_path.exists():
            print(f"Loading raw Kaggle file from {raw_kaggle_path}...")
            raw_df = pd.read_csv(raw_kaggle_path)
        else:
            print("Raw creditcard.csv not present. Generating synthetic benchmark sample...")
            raw_df = generate_sample_kaggle_data(n_samples=1000)

        adapter = KaggleCreditCardAdapter(
            start_date=sim_cfg.get("start_date", "2018-04-01"),
            n_customers=sim_cfg.get("n_customers", 50),
            n_terminals=sim_cfg.get("n_terminals", 100),
        )
        transactions = adapter.transform(raw_df)
        customers = generate_customer_profiles_table(sim_cfg.get("n_customers", 50), sim_cfg.get("random_seed", 42))
        terminals = generate_terminal_profiles_table(sim_cfg.get("n_terminals", 100), sim_cfg.get("random_seed", 42))

    elif source == "ieee_cis":
        print("Ingesting IEEE-CIS Fraud Detection benchmark dataset...")
        raw_ieee_path = raw_dir / "train_transaction.csv"
        if raw_ieee_path.exists():
            print(f"Loading raw IEEE-CIS file from {raw_ieee_path}...")
            raw_df = pd.read_csv(raw_ieee_path)
        else:
            print("Raw train_transaction.csv not present. Generating synthetic benchmark sample...")
            raw_df = generate_sample_ieee_cis_data(n_samples=1000)

        adapter = IEEECISAdapter(
            start_date=sim_cfg.get("start_date", "2018-04-01"),
            n_customers=sim_cfg.get("n_customers", 50),
            n_terminals=sim_cfg.get("n_terminals", 100),
        )
        transactions = adapter.transform(raw_df)
        customers = generate_customer_profiles_table(sim_cfg.get("n_customers", 50), sim_cfg.get("random_seed", 42))
        terminals = generate_terminal_profiles_table(sim_cfg.get("n_terminals", 100), sim_cfg.get("random_seed", 42))

    else:
        print(f"Generating vectorized simulation for {sim_cfg['n_customers']} customers, {sim_cfg['n_terminals']} terminals, {sim_cfg['nb_days']} days...")
        t0 = time.time()
        customers, terminals, transactions = generate_dataset(
            n_customers=sim_cfg['n_customers'],
            n_terminals=sim_cfg['n_terminals'],
            nb_days=sim_cfg['nb_days'],
            start_date=sim_cfg['start_date'],
            r=sim_cfg['radius'],
            random_state=sim_cfg['random_seed']
        )
        print(f"Raw simulation generated in {time.time() - t0:.2f}s")
        
        print("Adding fraud scenarios...")
        transactions = add_frauds(customers, terminals, transactions, sim_cfg['nb_days'], sim_cfg['random_seed'])

    # Validate
    assert 'TX_FRAUD' in transactions.columns
    assert 'TX_FRAUD_SCENARIO' in transactions.columns
    assert transactions['TX_FRAUD'].isin([0,1]).all()
    
    print("Saving to disk...")
    customers.to_pickle(raw_dir / 'customer_profiles.pkl')
    terminals.to_pickle(raw_dir / 'terminal_profiles.pkl')
    transactions.to_pickle(raw_dir / 'transactions.pkl')
    
    print(f"--- Dataset Summary ({source.upper()}) ---")
    print(f"Total transactions: {len(transactions):,}")
    frauds = int(transactions['TX_FRAUD'].sum())
    print(f"Total frauds: {frauds:,} ({frauds/len(transactions)*100:.2f}%)")
    print(f"Scenarios breakdown:")
    print(transactions['TX_FRAUD_SCENARIO'].value_counts())
    print("Done!")

if __name__ == "__main__":
    main()
