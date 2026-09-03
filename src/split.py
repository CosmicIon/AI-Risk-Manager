import pandas as pd
from src.utils import get_project_root, load_config

def main():
    print("Running Train/Test Split (Module 3)...")
    config = load_config()
    split_cfg = config['split']
    
    root = get_project_root()
    proc_dir = root / 'data' / 'processed'
    
    print("Loading engineered features...")
    features = pd.read_parquet(proc_dir / 'features.parquet')
    
    train_end_day = split_cfg['train_end_day']
    test_start_day = split_cfg['test_start_day']
    
    print(f"Splitting data: train <= {train_end_day}, test >= {test_start_day}")
    
    train = features[features['TX_TIME_DAYS'] <= train_end_day]
    test = features[features['TX_TIME_DAYS'] >= test_start_day]
    
    # Validations
    assert train['TX_TIME_DAYS'].max() <= train_end_day
    assert test['TX_TIME_DAYS'].min() >= test_start_day
    assert len(train) > 0 and len(test) > 0
    assert train['TX_FRAUD'].sum() > 0 and test['TX_FRAUD'].sum() > 0
    
    print(f"--- Split Summary ---")
    print(f"Train rows: {len(train):,}")
    print(f"Test rows: {len(test):,}")
    print(f"Train fraud rate: {train['TX_FRAUD'].mean()*100:.2f}%")
    print(f"Test fraud rate: {test['TX_FRAUD'].mean()*100:.2f}%")
    print(f"Train date range: {train['TX_DATETIME'].min().date()} to {train['TX_DATETIME'].max().date()}")
    print(f"Test date range: {test['TX_DATETIME'].min().date()} to {test['TX_DATETIME'].max().date()}")
    
    print("Saving splits...")
    train.to_parquet(proc_dir / 'train.parquet')
    test.to_parquet(proc_dir / 'test.parquet')
    print("Split complete!")

if __name__ == "__main__":
    main()
