import argparse
import json
import os
from datetime import datetime

import lightgbm as lgb
import pandas as pd
from onnxmltools.convert import convert_lightgbm
from onnxmltools.convert.common.data_types import FloatTensorType
from sklearn.model_selection import train_test_split

from src.ml.models.return_risk.config import CATEGORICAL_FEATURES, FEATURE_NAMES, HYPERPARAMETERS
from src.ml.models.return_risk.features import compute_features


def load_and_prepare_data(data_path: str):
    print(f"Loading data from {data_path}...")
    df = pd.read_parquet(data_path)

    print("Extracting features...")
    # In a real pipeline, we'd have historical aggregations.
    # Here, we map the columns to the feature vector.
    features_list = []
    for _, row in df.iterrows():
        order = {
            "order_date": row["order_date"],
            "category": row["category"],
            "return_amount": row["return_amount"],
            "order_amount": row["order_amount"],
        }
        feats = compute_features(row["customer_id"], order, [])
        features_list.append(feats)

    X = pd.DataFrame(features_list)[FEATURE_NAMES]
    y = df["is_abusive"].astype(int)

    return X, y


def train(X, y) -> lgb.Booster:
    print("Training LightGBM model...")
    # Change categorical features to category dtype for LightGBM
    for cat in CATEGORICAL_FEATURES:
        if cat in X.columns:
            X[cat] = X[cat].astype("category")

    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=HYPERPARAMETERS["seed"]
    )

    train_data = lgb.Dataset(X_train, label=y_train, categorical_feature=CATEGORICAL_FEATURES)
    val_data = lgb.Dataset(
        X_val, label=y_val, categorical_feature=CATEGORICAL_FEATURES, reference=train_data
    )

    booster = lgb.train(
        HYPERPARAMETERS,
        train_data,
        valid_sets=[train_data, val_data],
        callbacks=[lgb.early_stopping(stopping_rounds=50)],
    )
    return booster


def export_to_onnx(booster: lgb.Booster, output_path: str):
    print(f"Exporting model to {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    initial_types = [("float_input", FloatTensorType([None, len(FEATURE_NAMES)]))]
    onnx_model = convert_lightgbm(booster, initial_types=initial_types, target_opset=12)

    with open(output_path, "wb") as f:
        f.write(onnx_model.SerializeToString())


def save_metadata(output_dir: str, train_metrics: dict):
    metadata = {
        "model_name": "return_risk",
        "version": "v1",
        "trained_at": datetime.now().isoformat(),
        "feature_names": FEATURE_NAMES,
        "hyperparameters": HYPERPARAMETERS,
        "metrics": train_metrics,
    }
    with open(os.path.join(output_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", required=True, help="Path to returns.parquet")
    parser.add_argument("--output", required=True, help="Output directory for model")
    args = parser.parse_args()

    X, y = load_and_prepare_data(args.data)
    booster = train(X, y)

    os.makedirs(args.output, exist_ok=True)
    export_to_onnx(booster, os.path.join(args.output, "model.onnx"))

    # Save dummy metrics for now
    metrics = {"val_logloss": booster.best_score.get("valid_1", {}).get("binary_logloss", 0.0)}
    save_metadata(args.output, metrics)
    print("Training complete.")


if __name__ == "__main__":
    main()
