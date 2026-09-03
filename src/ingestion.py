import pandas as pd
import numpy as np
import random
import time
import os
from datetime import datetime, timedelta
from src.utils import load_config, get_project_root

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

def get_list_terminals_within_radius(customer_profile, x_y_terminals, r):
    x_y_customer = customer_profile[['x_customer_id','y_customer_id']].values.astype(float)
    squared_diff_x_y = np.square(x_y_customer - x_y_terminals)
    dist_x_y = np.sqrt(np.sum(squared_diff_x_y, axis=1))
    available_terminals = list(np.where(dist_x_y<r)[0])
    return available_terminals

def generate_transactions_table(customer_profile, start_date, nb_days):
    customer_transactions = []
    random.seed(int(customer_profile.CUSTOMER_ID))
    np.random.seed(int(customer_profile.CUSTOMER_ID))
    
    for day in range(nb_days):
        nb_tx = np.random.poisson(customer_profile.mean_nb_tx_per_day)
        if nb_tx>0:
            for tx in range(nb_tx):
                time_tx = int(np.random.normal(86400/2, 20000))
                if (time_tx<0) or (time_tx>=86400):
                    time_tx = int(np.random.uniform(0,86400))
                amount = np.random.normal(customer_profile.mean_amount, customer_profile.std_amount)
                if amount<0:
                    amount = np.random.uniform(0,customer_profile.mean_amount*2)
                amount = np.round(amount,decimals=2)
                
                if len(customer_profile.available_terminals)>0:
                    terminal_id = random.choice(customer_profile.available_terminals)
                    customer_transactions.append([time_tx+day*86400, day,
                                                  customer_profile.CUSTOMER_ID, 
                                                  terminal_id, amount])
            
    customer_transactions = pd.DataFrame(customer_transactions, columns=['TX_TIME_SECONDS', 'TX_TIME_DAYS', 'CUSTOMER_ID', 'TERMINAL_ID', 'TX_AMOUNT'])
    if len(customer_transactions)>0:
        start_date = pd.Timestamp(start_date)
        customer_transactions['TX_DATETIME'] = start_date + pd.to_timedelta(customer_transactions['TX_TIME_SECONDS'], unit='s')
    
    return customer_transactions

def generate_dataset(n_customers, n_terminals, nb_days, start_date, r, random_state=42):
    start_time = time.time()
    
    # 1. Profiles
    customer_profiles_table = generate_customer_profiles_table(n_customers, random_state)
    terminal_profiles_table = generate_terminal_profiles_table(n_terminals, random_state)
    
    # 2. Terminals associated to customers
    x_y_terminals = terminal_profiles_table[['x_terminal_id','y_terminal_id']].values.astype(float)
    customer_profiles_table['available_terminals'] = customer_profiles_table.apply(
        lambda x : get_list_terminals_within_radius(x, x_y_terminals=x_y_terminals, r=r), axis=1)
    
    # Customers with no terminals -> give them a random one
    customer_profiles_table.loc[customer_profiles_table.available_terminals.apply(len)==0, 'available_terminals'] = \
        pd.Series([[np.random.randint(0,n_terminals)] for i in range(len(customer_profiles_table))])
        
    # 3. Transactions
    transactions_df = customer_profiles_table.apply(
        lambda x : generate_transactions_table(x, start_date=start_date, nb_days=nb_days), axis=1)
    
    # concat all customer txs
    transactions_df = pd.concat(list(transactions_df), ignore_index=True)
    
    # Sort
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
    config = load_config()
    sim_cfg = config['simulator']
    
    print(f"Generating data for {sim_cfg['n_customers']} customers, {sim_cfg['n_terminals']} terminals, {sim_cfg['nb_days']} days...")
    
    customers, terminals, transactions = generate_dataset(
        n_customers=sim_cfg['n_customers'],
        n_terminals=sim_cfg['n_terminals'],
        nb_days=sim_cfg['nb_days'],
        start_date=sim_cfg['start_date'],
        r=sim_cfg['radius'],
        random_state=sim_cfg['random_seed']
    )
    
    print("Adding fraud scenarios...")
    transactions = add_frauds(customers, terminals, transactions, sim_cfg['nb_days'], sim_cfg['random_seed'])
    
    # Validate
    assert 'TX_FRAUD' in transactions.columns
    assert 'TX_FRAUD_SCENARIO' in transactions.columns
    assert transactions['TX_FRAUD'].isin([0,1]).all()
    
    print("Saving to disk...")
    root = get_project_root()
    raw_dir = root / 'data' / 'raw'
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    customers.to_pickle(raw_dir / 'customer_profiles.pkl')
    terminals.to_pickle(raw_dir / 'terminal_profiles.pkl')
    transactions.to_pickle(raw_dir / 'transactions.pkl')
    
    print(f"--- Dataset Summary ---")
    print(f"Total transactions: {len(transactions)}")
    frauds = transactions['TX_FRAUD'].sum()
    print(f"Total frauds: {frauds} ({frauds/len(transactions)*100:.2f}%)")
    print(f"Scenarios breakdown:")
    print(transactions['TX_FRAUD_SCENARIO'].value_counts())
    print("Done!")

if __name__ == "__main__":
    main()
