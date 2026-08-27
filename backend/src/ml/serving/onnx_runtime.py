import time

import numpy as np
import onnxruntime as ort

from src.core.exceptions import ModelInferenceError


class ONNXModelServer:
    def __init__(self, model_path: str):
        try:
            self.session = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])
            self.input_name = self.session.get_inputs()[0].name
            self.input_shape = self.session.get_inputs()[0].shape
        except Exception as e:
            raise ModelInferenceError(f"Failed to load ONNX model at {model_path}: {e}") from e

    def predict(self, features: np.ndarray) -> np.ndarray:
        try:
            # Expected input is a float tensor
            inputs = {self.input_name: features.astype(np.float32)}
            outputs = self.session.run(None, inputs)

            # Usually LightGBM ONNX export outputs [label, probabilities]
            # Probabilities is a list of dicts. We extract the prob for class 1
            if len(outputs) > 1 and isinstance(outputs[1], list):
                if isinstance(outputs[1][0], dict):
                    return np.array([p[1] for p in outputs[1]])

            # Default fallback for other models (e.g. isolation forest or LSTM)
            return outputs[0]
        except Exception as e:
            raise ModelInferenceError(f"Inference failed: {e}") from e

    def predict_with_latency(self, features: np.ndarray) -> tuple[np.ndarray, float]:
        start = time.perf_counter_ns()
        preds = self.predict(features)
        latency_ms = (time.perf_counter_ns() - start) / 1_000_000
        return preds, latency_ms

    def get_input_shape(self) -> tuple:
        return self.input_shape

    def health_check(self) -> bool:
        try:
            # Determine dummy shape
            shape = [1 if isinstance(s, str) or s is None else s for s in self.input_shape]
            if len(shape) == 0 or shape[0] == 0:
                shape = [1, 50]  # fallback for testing

            dummy = np.random.randn(*shape).astype(np.float32)
            self.predict(dummy)
            return True
        except Exception:
            return False
