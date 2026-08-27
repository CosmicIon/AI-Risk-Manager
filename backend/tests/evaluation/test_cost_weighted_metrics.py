import numpy as np
from decimal import Decimal

from src.ml.evaluation.metrics import (
    compute_binary_metrics,
    find_optimal_threshold,
    compute_calibration_curve,
    compute_threshold_curve
)

def test_cost_weighted_loss_calculation():
    # 10 samples total
    # fp=2, fn=1, tp=4, tn=3
    # fp_cost = 500, fn_cost = 2000
    # Expected cost_weighted_loss = (2 * 500 + 1 * 2000) / 10 = 3000 / 10 = 300.0
    
    y_true = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
    
    # 4 TPs, 1 FN (positives) -> pred positives at indices 0,1,2,3 (1 at index 4)
    # 2 FPs, 3 TNs (negatives) -> pred positives at indices 5,6 (0 at index 7,8,9)
    y_prob = np.array([0.9, 0.8, 0.7, 0.6, 0.4, 0.9, 0.8, 0.4, 0.3, 0.1])
    
    fp_cost = Decimal("500")
    fn_cost = Decimal("2000")
    
    metrics = compute_binary_metrics(y_true, y_prob, 0.5, fp_cost, fn_cost)
    
    assert metrics.tp_count == 4
    assert metrics.fn_count == 1
    assert metrics.fp_count == 2
    assert metrics.tn_count == 3
    
    assert metrics.total_fp_cost == Decimal("1000")
    assert metrics.total_fn_cost == Decimal("2000")
    assert metrics.cost_weighted_loss == 300.0


def test_find_optimal_threshold():
    # Similar setup, but we'll try to see if it picks a threshold that minimizes loss
    y_true = np.array([1, 1, 1, 1, 1, 0, 0, 0, 0, 0])
    y_prob = np.array([0.9, 0.8, 0.7, 0.6, 0.4, 0.9, 0.8, 0.4, 0.3, 0.1])
    
    fp_cost = 500
    fn_cost = 2000
    
    # At t=0.5: loss = 300
    # At t=0.85: TP=1, FN=4, FP=1, TN=4 -> FP_cost=500, FN_cost=8000 -> total=8500 -> loss=850
    # At t=0.35: TP=5, FN=0, FP=3, TN=2 -> FP_cost=1500, FN_cost=0 -> total=1500 -> loss=150
    
    thresholds = np.array([0.35, 0.5, 0.85])
    best_threshold, best_metrics = find_optimal_threshold(
        y_true, y_prob, fp_cost, fn_cost, thresholds=thresholds
    )
    
    assert best_threshold == 0.35
    assert best_metrics.cost_weighted_loss == 150.0
    assert best_metrics.fn_count == 0
    assert best_metrics.fp_count == 3


def test_compute_calibration_curve():
    y_true = np.array([1, 1, 0, 0, 1, 0, 1, 0, 0, 1])
    y_prob = np.array([0.9, 0.8, 0.1, 0.2, 0.7, 0.3, 0.6, 0.4, 0.2, 0.5])
    
    curve = compute_calibration_curve(y_true, y_prob, n_bins=5)
    
    assert "bin_means" in curve
    assert "fraction_positive" in curve
    assert "ece" in curve
    assert isinstance(curve["ece"], float)
