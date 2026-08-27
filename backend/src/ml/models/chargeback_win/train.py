import os
import json
import argparse
from datetime import datetime
import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from onnxmltools.convert import convert_lightgbm
from onnxmltools.convert.common.data_types import FloatTensorType

from src.ml.models.chargeback_win.features import FEATURE_NAMES, compute_features

HYPERPARAMETERS = {
    "objective": "binary",
    "metric": "binary_logloss",
    "learning_rate": 0.05,
    "n_estimators": 200,
    "seed": 42
}

def load_and_prepare_data(data_path: str):
    print(f"Loading chargeback data from {data_path}...")
    df = pd.read_parquet(data_path)
    
    # Drop pending cases for training
    df = df[df["outcome"] != "PENDING"]
    
    features_list = []
    for _, row in df.iterrows():
        # Mock evidence 
        evidence = {"items": [], "completeness_score": np.random.random()}
        feats = compute_features(row.to_dict(), evidence)
        features_list.append(feats)
        
    X = pd.DataFrame(features_list)[FEATURE_NAMES]
    y = (df["outcome"] == "WON").astype(int)
    
    return X, y

def train(X, y) -> lgb.Booster:
    print("Training LightGBM model for chargeback win prob...")
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=HYPERPARAMETERS["seed"])
    
    train_data = lgb.Dataset(X_train, label=y_train)
    val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
    
    booster = lgb.train(
        HYPERPARAMETERS,
        train_data,
        valid_sets=[train_data, val_data],
        callbacks=[lgb.early_stopping(stopping_rounds=20)]
    )
    return booster

def export_to_onnx(booster: lgb.Booster, output_path: str):
    print(f"Exporting model to {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    initial_types = [('float_input', FloatTensorType([None, len(FEATURE_NAMES)]))]
    onnx_model = convert_lightgbm(booster, initial_types=initial_types, target_opset=12)
    
    with open(output_path, "wb") as f:
        f.write(onnx_model.SerializeToString())

def save_metadata(output_dir: str, train_metrics: dict):
    metadata = {
        "model_name": "chargeback_win",
        "version": "v1",
        "trained_at": datetime.now().isoformat(),
        "feature_names": FEATURE_NAMES,
        "hyperparameters": HYPERPARAMETERS,
        "metrics": train_metrics
    }
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to chargebacks.parquet")
    parser.add_argument("--output", required=True, help="Output directory for model")
    args = parser.parse_args()
    
    X, y = load_and_prepare_data(args.data)
    booster = train(X, y)
    
    os.makedirs(args.output, exist_ok=True)
    export_to_onnx(booster, os.path.join(args.output, "model.onnx"))
    
    metrics = {"val_logloss": booster.best_score.get("valid_1", {}).get("binary_logloss", 0.0)}
    save_metadata(args.output, metrics)
    print("Training complete.")

if __name__ == "__main__":
    main()
