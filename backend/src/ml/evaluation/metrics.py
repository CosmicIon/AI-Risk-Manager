from decimal import Decimal

import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score

from src.core.schemas.evaluation import CostWeightedMetrics


def compute_binary_metrics(
    y_true: np.ndarray, y_prob: np.ndarray, threshold: float, fp_cost: Decimal, fn_cost: Decimal
) -> CostWeightedMetrics:
    """
    Compute binary classification metrics and cost-weighted metrics at a given threshold.
    """
    y_pred = (y_prob >= threshold).astype(int)

    # Calculate standard metrics
    # zero_division=0 to handle cases where there are no positive predictions
    precision = float(precision_score(y_true, y_pred, zero_division=0))
    recall = float(recall_score(y_true, y_pred, zero_division=0))
    f1 = float(f1_score(y_true, y_pred, zero_division=0))

    # Handle cases where all true labels are the same (e.g. only 0 or 1)
    if len(np.unique(y_true)) > 1:
        auc_roc = float(roc_auc_score(y_true, y_prob))
    else:
        auc_roc = 0.5

    # Compute confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()

    return CostWeightedMetrics(
        precision=precision,
        recall=recall,
        f1=f1,
        auc_roc=auc_roc,
        fp_count=int(fp),
        fn_count=int(fn),
        tp_count=int(tp),
        tn_count=int(tn),
        fp_cost_per_unit=fp_cost,
        fn_cost_per_unit=fn_cost,
    )


def find_optimal_threshold(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    fp_cost: float | Decimal,
    fn_cost: float | Decimal,
    thresholds: np.ndarray = np.arange(0.05, 0.95, 0.01)
) -> tuple[float, CostWeightedMetrics]:
    """
    Sweep thresholds and return the one minimizing cost-weighted loss.
    """
    best_threshold = 0.5
    best_metrics = None
    min_loss = float('inf')

    fp_cost_dec = Decimal(str(fp_cost))
    fn_cost_dec = Decimal(str(fn_cost))

    for threshold in thresholds:
        metrics = compute_binary_metrics(y_true, y_prob, float(threshold), fp_cost_dec, fn_cost_dec)
        loss = metrics.cost_weighted_loss
        if loss < min_loss:
            min_loss = loss
            best_threshold = float(threshold)
            best_metrics = metrics

    # Fallback if thresholds list is empty or similar edge case
    if best_metrics is None:
        best_metrics = compute_binary_metrics(y_true, y_prob, 0.5, fp_cost_dec, fn_cost_dec)
        best_threshold = 0.5

    return best_threshold, best_metrics


def compute_calibration_curve(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> dict:
    """
    Compute expected calibration error and return bins.
    """
    fraction_positive, bin_means = calibration_curve(y_true, y_prob, n_bins=n_bins, strategy='uniform')

    # Calculate Expected Calibration Error (ECE)
    # Re-implementing a simple ECE since it's not directly in sklearn
    # Bin predictions
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    binned = np.digitize(y_prob, bins) - 1

    ece = 0.0
    for i in range(n_bins):
        bin_idx = (binned == i)
        bin_count = np.sum(bin_idx)
        if bin_count > 0:
            bin_acc = np.mean(y_true[bin_idx])
            bin_conf = np.mean(y_prob[bin_idx])
            ece += (bin_count / len(y_prob)) * np.abs(bin_acc - bin_conf)

    return {
        "bin_means": bin_means.tolist(),
        "fraction_positive": fraction_positive.tolist(),
        "ece": float(ece)
    }


def compute_threshold_curve(
    y_true: np.ndarray,
    y_prob: np.ndarray,
    fp_cost: float | Decimal,
    fn_cost: float | Decimal,
    thresholds: np.ndarray = np.arange(0.05, 0.95, 0.05)
) -> list[dict]:
    """
    Returns array of threshold metrics for dashboard visualization.
    """
    fp_cost_dec = Decimal(str(fp_cost))
    fn_cost_dec = Decimal(str(fn_cost))

    results = []
    for threshold in thresholds:
        metrics = compute_binary_metrics(y_true, y_prob, float(threshold), fp_cost_dec, fn_cost_dec)
        results.append({
            "threshold": float(threshold),
            "precision": metrics.precision,
            "recall": metrics.recall,
            "cost_weighted_loss": metrics.cost_weighted_loss
        })
    return results
