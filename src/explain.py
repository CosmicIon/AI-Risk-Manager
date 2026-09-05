# pyrefly: ignore [missing-import]
import shap
import joblib
import json
import pandas as pd
import numpy as np
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from src.utils import get_project_root

class RiskExplainer:
    def __init__(self):
        root = get_project_root()
        models_dir = root / 'models'
        
        self.model = joblib.load(models_dir / 'model.pkl')
        with open(models_dir / 'feature_columns.json', 'r') as f:
            self.features = json.load(f)
            
        with open(models_dir / 'metrics_test.json', 'r') as f:
            metrics = json.load(f)
            self.threshold = metrics['recommended_threshold']
            
        # One-time explainer setup
        self.explainer = shap.TreeExplainer(self.model)
        
    def _translate_feature(self, feature_name, value):
        """Map raw feature names to plain English phrases (defense-only)"""
        if feature_name == 'TX_AMOUNT':
            return f"The transaction amount (${value:.2f})"
        if feature_name == 'TX_DURING_WEEKEND':
            return "This transaction was on a weekend" if value == 1 else "This transaction was on a weekday"
        if feature_name == 'TX_DURING_NIGHT':
            return "This transaction was late at night" if value == 1 else "This transaction was during the day"
        if 'CUSTOMER_ID_AVG_AMOUNT' in feature_name:
            window = feature_name.split('_')[-2].replace('DAY', '')
            return f"This customer's average spend over the past {window} days"
        if 'CUSTOMER_ID_NB_TX' in feature_name:
            window = feature_name.split('_')[-2].replace('DAY', '')
            return f"The number of transactions by this customer in the past {window} days"
        if 'CUSTOMER_ID_STD_AMOUNT' in feature_name:
            return "The variability in this customer's spending"
        if 'TERMINAL_ID_RISK' in feature_name:
            window = feature_name.split('_')[-2].replace('DAY', '')
            return f"This terminal has an unusually high fraud rate in the past {window} days"
        if 'TERMINAL_ID_NB_TX' in feature_name:
            window = feature_name.split('_')[-2].replace('DAY', '')
            return f"The activity level of this terminal in the past {window} days"
        if feature_name == 'TX_AMOUNT_ZSCORE':
            if value > 3:
                return "This amount is significantly higher than what this customer normally spends"
            elif value < -3:
                return "This amount is significantly lower than what this customer normally spends"
            else:
                return "How this amount compares to the customer's typical spend"
        if feature_name == 'TX_DIST_CUSTOMER_TERMINAL':
            if value > 15:
                return f"This transaction terminal is unusually far ({value:.1f} km) from the customer's normal location"
            else:
                return f"The physical distance to this terminal ({value:.1f} km)"
        if feature_name == 'CUSTOMER_ID_NB_TX_15MIN_WINDOW':
            return "Multiple rapid transactions were initiated within the last 15 minutes"
        if feature_name == 'CUSTOMER_ID_NB_TX_1HOUR_WINDOW':
            return "Unusually high frequency of transactions in the past hour"
        if feature_name == 'TIME_SINCE_LAST_TX':
            if value < 60:
                return "This transaction occurred within seconds of the customer's previous purchase"
            else:
                return "The time gap since the customer's previous purchase"
                
        return feature_name.replace('_', ' ').lower()
        
    def score_transaction(self, tx_row: pd.Series) -> tuple[float, str]:
        # Extract features
        x = tx_row[self.features].to_frame().T.astype(float)
        prob = self.model.predict_proba(x)[0, 1]
        
        if prob >= self.threshold:
            risk_level = "High"
        elif prob >= self.threshold / 2:
            risk_level = "Medium"
        else:
            risk_level = "Low"
            
        return prob, risk_level

    def explain_transaction(self, tx_row: pd.Series):
        x = tx_row[self.features].to_frame().T.astype(float)
        prob, risk_level = self.score_transaction(tx_row)
        
        shap_values = self.explainer.shap_values(x)[1][0] if isinstance(self.explainer.shap_values(x), list) else self.explainer.shap_values(x)[0]
        
        # Zip features with shap values
        feature_impacts = list(zip(self.features, shap_values, x.iloc[0].values))
        
        # Sort by absolute impact
        feature_impacts.sort(key=lambda item: abs(item[1]), reverse=True)
        
        top_reasons = []
        for feat, impact, val in feature_impacts[:3]:
            if abs(impact) < 0.01:
                continue # Skip negligible features
                
            direction = "increased" if impact > 0 else "decreased"
            phrase = self._translate_feature(feat, val)
            
            # Special case for pre-computed sentences
            if "significantly higher" in phrase or "unusually high fraud rate" in phrase:
                if impact > 0:
                    top_reasons.append(phrase)
                else:
                    top_reasons.append(f"{phrase} ({direction} risk score)")
            else:
                top_reasons.append(f"{phrase} {direction} the risk score.")
                
        if not top_reasons:
            top_reasons.append("No single factor strongly contributed to this score — the transaction appears routine.")
            
        return {
            "score": float(prob),
            "risk_level": risk_level,
            "top_reasons": top_reasons,
            "shap_values": dict(zip(self.features, shap_values)),
            "base_value": float(self.explainer.expected_value[1] if isinstance(self.explainer.expected_value, list) else self.explainer.expected_value)
        }
