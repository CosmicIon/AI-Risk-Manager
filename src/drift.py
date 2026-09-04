"""
Module: Model Drift & Production Monitoring (Population Stability Index & Concept Drift)
Calculates feature-level PSI, prediction probability drift, and concept drift (fraud prevalence shift)
between training baseline and production test sets. Generates executive reports and actionable alerts.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import numpy as np
import pandas as pd

from src.utils import get_project_root, load_config


def calculate_feature_psi(
    expected: np.ndarray,
    actual: np.ndarray,
    num_bins: int = 10,
    epsilon: float = 1e-4,
) -> Tuple[float, pd.DataFrame]:
    """
    Calculates the Population Stability Index (PSI) between a baseline (expected)
    and target (actual) continuous or numerical distribution.
    
    Formula:
        PSI = sum((Actual% - Expected%) * ln(Actual% / Expected%))
    """
    expected = np.asarray(expected, dtype=float)
    actual = np.asarray(actual, dtype=float)

    # Filter out NaNs
    expected = expected[~np.isnan(expected)]
    actual = actual[~np.isnan(actual)]

    if len(expected) == 0 or len(actual) == 0:
        return 0.0, pd.DataFrame()

    # Determine quantile bins based on the baseline distribution
    percentiles = np.linspace(0, 100, num_bins + 1)
    bins = np.percentile(expected, percentiles)
    bins = np.unique(bins)

    if len(bins) < 2:
        # Constant or non-varying feature
        return 0.0, pd.DataFrame()

    bins[0] = -np.inf
    bins[-1] = np.inf

    # Bin counts
    exp_counts, _ = np.histogram(expected, bins=bins)
    act_counts, _ = np.histogram(actual, bins=bins)

    # Convert to proportions with epsilon smoothing to prevent div by zero / log(0)
    exp_pct = (exp_counts / len(expected)) + epsilon
    act_pct = (act_counts / len(actual)) + epsilon

    # Re-normalize to sum to 1.0
    exp_pct = exp_pct / np.sum(exp_pct)
    act_pct = act_pct / np.sum(act_pct)

    bin_psi = (act_pct - exp_pct) * np.log(act_pct / exp_pct)
    total_psi = float(np.sum(bin_psi))

    breakdown = pd.DataFrame(
        {
            "bin": range(1, len(bins)),
            "expected_pct": np.round(exp_pct * 100, 2),
            "actual_pct": np.round(act_pct * 100, 2),
            "bin_psi": np.round(bin_psi, 4),
        }
    )

    return round(total_psi, 4), breakdown


def classify_psi(psi: float) -> str:
    """Classifies PSI value into industry-standard risk tiers."""
    if psi < 0.10:
        return "STABLE"
    elif psi <= 0.25:
        return "MODERATE_SHIFT"
    else:
        return "SIGNIFICANT_DRIFT"


def calculate_dataset_drift(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_cols: List[str],
    target_col: str = "TX_FRAUD",
    model: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Computes feature PSI, concept drift, and prediction drift across the entire dataset.
    """
    feature_results = []
    significant_count = 0
    moderate_count = 0
    stable_count = 0

    for col in feature_cols:
        if col not in train_df.columns or col not in test_df.columns:
            continue

        exp_vals = train_df[col].values
        act_vals = test_df[col].values

        psi_val, _ = calculate_feature_psi(exp_vals, act_vals)
        status = classify_psi(psi_val)

        if status == "SIGNIFICANT_DRIFT":
            significant_count += 1
        elif status == "MODERATE_SHIFT":
            moderate_count += 1
        else:
            stable_count += 1

        feature_results.append(
            {
                "feature": col,
                "psi": psi_val,
                "status": status,
                "train_mean": round(float(np.mean(exp_vals)), 4),
                "test_mean": round(float(np.mean(act_vals)), 4),
                "train_std": round(float(np.std(exp_vals)), 4),
                "test_std": round(float(np.std(act_vals)), 4),
            }
        )

    # Sort descending by PSI
    feature_results.sort(key=lambda x: x["psi"], reverse=True)

    # 1. Concept Drift (Target distribution shift)
    train_fraud_rate = float(train_df[target_col].mean() * 100) if target_col in train_df else 0.0
    test_fraud_rate = float(test_df[target_col].mean() * 100) if target_col in test_df else 0.0
    fraud_rate_shift_pct = round(test_fraud_rate - train_fraud_rate, 2)

    # 2. Prediction Drift (Score distribution shift)
    pred_psi = None
    pred_status = "N/A"
    if model is not None and set(feature_cols).issubset(train_df.columns) and set(feature_cols).issubset(test_df.columns):
        try:
            train_preds = model.predict_proba(train_df[feature_cols])[:, 1]
            test_preds = model.predict_proba(test_df[feature_cols])[:, 1]
            pred_psi, _ = calculate_feature_psi(train_preds, test_preds)
            pred_status = classify_psi(pred_psi)
        except Exception:
            pass

    # Overall system health
    if significant_count > 0:
        overall_health = "ACTION_REQUIRED"
        recommendation = (
            f"Retraining recommended: {significant_count} feature(s) show significant drift (PSI > 0.25). "
            f"Review data sources and schedule model update."
        )
    elif moderate_count > 0:
        overall_health = "MONITOR"
        recommendation = (
            f"Monitoring recommended: {moderate_count} feature(s) show moderate shift (0.10 <= PSI <= 0.25). "
            f"No immediate retraining needed."
        )
    else:
        overall_health = "HEALTHY"
        recommendation = "All features are stable (PSI < 0.10). Model remains robust for production inference."

    return {
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "overall_health": overall_health,
        "recommendation": recommendation,
        "train_samples": len(train_df),
        "test_samples": len(test_df),
        "feature_summary": {
            "total_features": len(feature_results),
            "stable": stable_count,
            "moderate_shift": moderate_count,
            "significant_drift": significant_count,
        },
        "concept_drift": {
            "train_fraud_rate_pct": round(train_fraud_rate, 2),
            "test_fraud_rate_pct": round(test_fraud_rate, 2),
            "shift_pct_points": fraud_rate_shift_pct,
            "status": "SIGNIFICANT_DRIFT" if abs(fraud_rate_shift_pct) > 10.0 else "STABLE",
        },
        "prediction_drift": {
            "psi": pred_psi,
            "status": pred_status,
        },
        "features": feature_results,
    }


def generate_drift_report(drift_summary: Dict[str, Any], output_dir: Path) -> Tuple[Path, Path]:
    """
    Exports a clean Markdown report and JSON metrics file to output_dir.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "drift_report.md"
    json_path = output_dir / "drift_metrics.json"

    # Save JSON metrics
    with open(json_path, "w") as f:
        json.dump(drift_summary, f, indent=4)

    # Build Markdown document
    health_badges = {
        "HEALTHY": "🟢 **HEALTHY** (Distributions Stable)",
        "MONITOR": "🟡 **MONITOR** (Moderate Shift Detected)",
        "ACTION_REQUIRED": "🔴 **ACTION REQUIRED** (Significant Drift Detected)",
    }
    badge = health_badges.get(drift_summary["overall_health"], drift_summary["overall_health"])

    lines = [
        "# 🛡️ Production Model Drift & Stability Report",
        "",
        f"**Generated:** `{drift_summary['timestamp']}`  ",
        f"**System Status:** {badge}  ",
        f"**Recommendation:** {drift_summary['recommendation']}",
        "",
        "---",
        "",
        "## 📊 Executive Monitoring Overview",
        "",
        "| Metric | Training Baseline | Production Test | Delta / PSI | Status |",
        "| :--- | :---: | :---: | :---: | :---: |",
        f"| **Sample Volume** | {drift_summary['train_samples']:,} tx | {drift_summary['test_samples']:,} tx | - | - |",
        f"| **Fraud Prevalence** | {drift_summary['concept_drift']['train_fraud_rate_pct']}% | {drift_summary['concept_drift']['test_fraud_rate_pct']}% | {drift_summary['concept_drift']['shift_pct_points']:+}% | `{drift_summary['concept_drift']['status']}` |",
    ]

    if drift_summary["prediction_drift"]["psi"] is not None:
        p_psi = drift_summary["prediction_drift"]["psi"]
        p_stat = drift_summary["prediction_drift"]["status"]
        lines.append(f"| **Prediction Score Drift** | Baseline Scores | Production Scores | PSI = {p_psi:.4f} | `{p_stat}` |")

    lines.extend([
        "",
        "---",
        "",
        "## 🔍 Feature-Level Population Stability Index (PSI)",
        "",
        "> **PSI Reference Thresholds:**  ",
        "> - $\\text{PSI} < 0.10$: 🟢 **STABLE** (Minimal distribution change)  ",
        "> - $0.10 \\le \\text{PSI} \\le 0.25$: 🟡 **MODERATE_SHIFT** (Monitor trends)  ",
        "> - $\\text{PSI} > 0.25$: 🔴 **SIGNIFICANT_DRIFT** (Action required: Model retraining recommended)  ",
        "",
        "| Feature | PSI Score | Status | Train Mean ± Std | Test Mean ± Std |",
        "| :--- | :---: | :---: | :---: | :---: |",
    ])

    status_emojis = {
        "STABLE": "🟢 STABLE",
        "MODERATE_SHIFT": "🟡 MODERATE",
        "SIGNIFICANT_DRIFT": "🔴 DRIFT ALERT",
    }

    for f in drift_summary["features"]:
        emoji_stat = status_emojis.get(f["status"], f["status"])
        train_stat = f"{f['train_mean']:.2f} ± {f['train_std']:.2f}"
        test_stat = f"{f['test_mean']:.2f} ± {f['test_std']:.2f}"
        lines.append(f"| `{f['feature']}` | **{f['psi']:.4f}** | {emoji_stat} | {train_stat} | {test_stat} |")

    lines.extend([
        "",
        "---",
        "",
        "## 🛠️ Automated Retraining Policy",
        "1. **Trigger Condition:** If $\\ge 2$ core features exceed $\\text{PSI} > 0.25$ OR prediction score $\\text{PSI} > 0.25$, initiate automated walk-forward retraining (`python -m src.train --cv`).",
        "2. **Data Pipeline Action:** If terminal risk or distance metrics drift, verify upstream geolocation lookups and feature windowing latency.",
        "",
    ])

    report_content = "\n".join(lines)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    return report_path, json_path


def run_drift_analysis(
    train_df: Optional[pd.DataFrame] = None,
    test_df: Optional[pd.DataFrame] = None,
    feature_cols: Optional[List[str]] = None,
    output_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """
    Main entry point for calculating dataset drift and exporting the report.
    """
    root = get_project_root()
    proc_dir = root / "data" / "processed"
    models_dir = root / "models"
    if output_dir is None:
        output_dir = root / "reports"

    if train_df is None:
        train_path = proc_dir / "train.parquet"
        if not train_path.exists():
            raise FileNotFoundError(f"Train split not found at {train_path}")
        train_df = pd.read_parquet(train_path)

    if test_df is None:
        test_path = proc_dir / "test.parquet"
        if not test_path.exists():
            raise FileNotFoundError(f"Test split not found at {test_path}")
        test_df = pd.read_parquet(test_path)

    if feature_cols is None:
        feats_path = models_dir / "feature_columns.json"
        if feats_path.exists():
            with open(feats_path, "r") as f:
                feature_cols = json.load(f)
        else:
            config = load_config()
            exclude = config.get("model", {}).get("exclude_cols_from_features", [])
            feature_cols = [c for c in train_df.columns if c not in exclude]

    model = None
    model_path = models_dir / "model.pkl"
    if model_path.exists():
        try:
            model = joblib.load(model_path)
        except Exception:
            pass

    print(
        f"\n{'='*75}\n"
        f"  POPULATION STABILITY INDEX (PSI) & CONCEPT DRIFT ANALYSIS\n"
        f"{'='*75}"
    )

    summary = calculate_dataset_drift(train_df, test_df, feature_cols, model=model)
    report_path, json_path = generate_drift_report(summary, output_dir)

    print(f"Overall Health: {summary['overall_health']}")
    print(f"Feature Breakdown: {summary['feature_summary']['stable']} Stable | {summary['feature_summary']['moderate_shift']} Moderate | {summary['feature_summary']['significant_drift']} Drift Alerts")
    print(f"Concept Drift (Fraud Rate): Train {summary['concept_drift']['train_fraud_rate_pct']}% -> Test {summary['concept_drift']['test_fraud_rate_pct']}% ({summary['concept_drift']['shift_pct_points']:+}%)")
    if summary["prediction_drift"]["psi"] is not None:
        print(f"Model Prediction PSI: {summary['prediction_drift']['psi']:.4f} ({summary['prediction_drift']['status']})")

    print(f"\n{'Feature':<35} | {'PSI':<8} | {'Status':<18} | {'Train -> Test Mean'}")
    print("-" * 80)
    for f in summary["features"][:10]:
        means = f"{f['train_mean']:.2f} -> {f['test_mean']:.2f}"
        print(f"{f['feature']:<35} | {f['psi']:<8.4f} | {f['status']:<18} | {means}")
    if len(summary["features"]) > 10:
        print(f"... ({len(summary['features']) - 10} more features in report)")
    print("-" * 80)

    print(f"\nSaved report to: {report_path}")
    print(f"Saved metrics to: {json_path}")

    return summary


if __name__ == "__main__":
    run_drift_analysis()
