import numpy as np
from skl2onnx import convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from sklearn.ensemble import IsolationForest


class IsolationForestDetector:
    def __init__(self, contamination=0.01, random_state=42):
        self.model = IsolationForest(contamination=contamination, random_state=random_state)

    def fit(self, X: np.ndarray):
        self.model.fit(X)

    def detect(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        # Returns (is_anomaly, anomaly_score)
        # sklearn returns 1 for inliers, -1 for outliers
        preds = self.model.predict(X)
        is_anomaly = (preds == -1)
        # decision_function: lower means more anomalous
        scores = self.model.decision_function(X)
        return is_anomaly, scores

    def export_to_onnx(self, output_path: str, num_features: int):
        initial_type = [('float_input', FloatTensorType([None, num_features]))]
        onx = convert_sklearn(self.model, initial_types=initial_type, target_opset=12)
        with open(output_path, "wb") as f:
            f.write(onx.SerializeToString())
