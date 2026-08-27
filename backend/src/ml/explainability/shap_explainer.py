import numpy as np
import shap
import lightgbm as lgb
from typing import Any

class SHAPExplainer:
    def __init__(self, model_path: str):
        # We need the native LightGBM model for SHAP TreeExplainer, not the ONNX one
        try:
            self.model = lgb.Booster(model_file=model_path)
            self.explainer = shap.TreeExplainer(self.model)
        except Exception as e:
            raise RuntimeError(f"Failed to load LightGBM model for SHAP: {e}")

    def explain(self, features: np.ndarray, feature_names: list[str], top_k: int = 5) -> list[dict[str, Any]]:
        # SHAP values for the input features
        shap_values = self.explainer.shap_values(features)
        
        # Binary classification usually returns a list of shape (num_classes, num_samples, num_features)
        # We want the values for the positive class [1]
        if isinstance(shap_values, list):
            vals = shap_values[1][0]
        else:
            vals = shap_values[0]
            
        # Get absolute values for sorting
        abs_vals = np.abs(vals)
        top_indices = np.argsort(abs_vals)[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            val = vals[idx]
            results.append({
                "feature": feature_names[idx],
                "shap_value": float(val),
                "direction": "increases_risk" if val > 0 else "decreases_risk"
            })
            
        return results
