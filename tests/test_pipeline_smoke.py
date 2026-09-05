import os
import subprocess
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils import get_project_root
import yaml

def test_pipeline_smoke():
    root = get_project_root()
    
    # 1. Override config to be tiny
    config_path = root / 'config.yaml'
    with open(config_path, 'r') as f:
        original_config = yaml.safe_load(f)
        
    tiny_config = original_config.copy()
    tiny_config['simulator']['n_customers'] = 50
    tiny_config['simulator']['n_terminals'] = 100
    tiny_config['simulator']['nb_days'] = 60
    tiny_config['split']['train_end_day'] = 45
    tiny_config['split']['test_start_day'] = 50
    
    try:
        with open(config_path, 'w') as f:
            yaml.dump(tiny_config, f)
            
        # 2. Run modules sequentially using current python executable
        modules = ['src.ingestion', 'src.features', 'src.split', 'src.train', 'src.evaluate']
        
        for mod in modules:
            result = subprocess.run([sys.executable, '-m', mod], cwd=root, capture_output=True, text=True)
            assert result.returncode == 0, f"Module {mod} failed:\n{result.stderr}\n{result.stdout}"
            
        # 3. Assert outputs exist
        assert (root / 'data' / 'raw' / 'transactions.pkl').exists()
        assert (root / 'data' / 'processed' / 'features.parquet').exists()
        assert (root / 'data' / 'processed' / 'train.parquet').exists()
        assert (root / 'data' / 'processed' / 'test.parquet').exists()
        assert (root / 'models' / 'model.pkl').exists()
        assert (root / 'models' / 'metrics_test.json').exists()
        
    finally:
        # Restore original config
        with open(config_path, 'w') as f:
            yaml.dump(original_config, f)
