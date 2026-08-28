from datetime import UTC, datetime

import numpy as np
import pandas as pd
from scipy.stats import entropy

from src.core.schemas.evaluation import DriftReport


class DriftDetector:
    def __init__(self, psi_threshold: float = 0.2, kl_threshold: float = 0.1):
        self.psi_threshold = psi_threshold
        self.kl_threshold = kl_threshold

    def compute_psi(self, expected: np.ndarray, actual: np.ndarray, buckets: int = 10) -> tuple[float, dict, dict]:
        """
        Compute Population Stability Index (PSI) between two arrays of numerical data.
        Returns (psi_value, expected_dist, actual_dist).
        """
        if len(expected) == 0 or len(actual) == 0:
            return 0.0, {}, {}

        # Define bins based on expected data quantiles to get equal sized buckets
        bins = np.percentile(expected, np.linspace(0, 100, buckets + 1))
        # Add small epsilon to max and min to include edge values
        bins[0] -= 1e-5
        bins[-1] += 1e-5

        # Calculate expected percentages
        expected_counts, _ = np.histogram(expected, bins=bins)
        expected_pct = expected_counts / len(expected)

        # Calculate actual percentages
        actual_counts, _ = np.histogram(actual, bins=bins)
        actual_pct = actual_counts / len(actual)

        # Avoid division by zero
        expected_pct = np.clip(expected_pct, 1e-4, 1.0)
        actual_pct = np.clip(actual_pct, 1e-4, 1.0)

        # Compute PSI
        psi_values = (actual_pct - expected_pct) * np.log(actual_pct / expected_pct)
        psi = float(np.sum(psi_values))

        # Format distributions for reporting
        exp_dist = {f"bin_{i}": float(v) for i, v in enumerate(expected_pct)}
        act_dist = {f"bin_{i}": float(v) for i, v in enumerate(actual_pct)}

        return psi, exp_dist, act_dist

    def compute_kl_divergence(self, expected: np.ndarray, actual: np.ndarray) -> tuple[float, dict, dict]:
        """
        Compute KL Divergence for categorical data.
        Returns (kl_value, expected_dist, actual_dist).
        """
        if len(expected) == 0 or len(actual) == 0:
            return 0.0, {}, {}

        # Get unique categories across both sets
        categories = np.unique(np.concatenate([expected, actual]))

        exp_counts = pd.Series(expected).value_counts()
        act_counts = pd.Series(actual).value_counts()

        exp_dist_arr = []
        act_dist_arr = []

        exp_dist_dict = {}
        act_dist_dict = {}

        for cat in categories:
            # Add small epsilon to avoid log(0)
            e_count = exp_counts.get(cat, 1e-4)
            a_count = act_counts.get(cat, 1e-4)

            exp_dist_arr.append(e_count)
            act_dist_arr.append(a_count)

            # For reporting, just use normal counts/percentages (no epsilon)
            exp_dist_dict[str(cat)] = float(exp_counts.get(cat, 0) / len(expected))
            act_dist_dict[str(cat)] = float(act_counts.get(cat, 0) / len(actual))

        exp_dist_arr = np.array(exp_dist_arr) / np.sum(exp_dist_arr)
        act_dist_arr = np.array(act_dist_arr) / np.sum(act_dist_arr)

        # Calculate KL Divergence: sum(P * log(P/Q)) where P=actual, Q=expected
        kl = float(entropy(act_dist_arr, exp_dist_arr))

        return kl, exp_dist_dict, act_dist_dict

    def detect_feature_drift(self, ref_data: pd.DataFrame, curr_data: pd.DataFrame, feature_cols: list[str]) -> list[DriftReport]:
        """
        Detect drift across multiple features. Numerical -> PSI, Categorical -> KL Divergence.
        """
        reports = []
        now = datetime.now(UTC)

        for col in feature_cols:
            if col not in ref_data.columns or col not in curr_data.columns:
                continue

            ref_vals = ref_data[col].dropna().values
            curr_vals = curr_data[col].dropna().values

            if len(ref_vals) == 0 or len(curr_vals) == 0:
                continue

            is_numeric = pd.api.types.is_numeric_dtype(ref_data[col])

            if is_numeric and len(np.unique(ref_vals)) > 10:
                # Use PSI for continuous numerical
                val, ref_dist, curr_dist = self.compute_psi(ref_vals, curr_vals)
                is_drifted = val > self.psi_threshold
                metric_type = "psi"
                psi_val = val
                kl_val = 0.0
            else:
                # Use KL Divergence for categorical or discrete numerical
                val, ref_dist, curr_dist = self.compute_kl_divergence(ref_vals, curr_vals)
                is_drifted = val > self.kl_threshold
                metric_type = "kl"
                kl_val = val
                psi_val = 0.0

            # Retrain recommended if drift is severe (e.g. 1.5x threshold)
            threshold = self.psi_threshold if metric_type == "psi" else self.kl_threshold
            requires_retrain = is_drifted and val > (threshold * 1.5)

            report = DriftReport(
                feature_name=col,
                psi_value=psi_val,
                kl_divergence=kl_val,
                is_drifted=is_drifted,
                requires_retrain=requires_retrain,
                reference_distribution=ref_dist,
                current_distribution=curr_dist,
                computed_at=now
            )
            reports.append(report)

        return reports

    def detect_prediction_drift(self, ref_preds: np.ndarray, curr_preds: np.ndarray) -> DriftReport:
        """
        Detect drift in model output predictions using PSI.
        """
        psi, ref_dist, curr_dist = self.compute_psi(ref_preds, curr_preds)
        is_drifted = psi > self.psi_threshold
        requires_retrain = is_drifted and psi > (self.psi_threshold * 1.5)

        return DriftReport(
            feature_name="model_predictions",
            psi_value=psi,
            kl_divergence=0.0,
            is_drifted=is_drifted,
            requires_retrain=requires_retrain,
            reference_distribution=ref_dist,
            current_distribution=curr_dist,
            computed_at=datetime.now(UTC)
        )
