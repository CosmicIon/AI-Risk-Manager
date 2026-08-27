import logging

import numpy as np

from src.core.exceptions import ModelInferenceError
from src.ml.serving.onnx_runtime import ONNXModelServer

logger = logging.getLogger(__name__)

class ModelRegistry:
    def __init__(self):
        # Format: "{model_name}:{version}" -> ONNXModelServer
        self.models: dict[str, ONNXModelServer] = {}
        # Format: "{model_name}" -> "version"
        self.champions: dict[str, str] = {}

    def load_model(self, model_name: str, version: str, model_path: str):
        key = f"{model_name}:{version}"
        try:
            self.models[key] = ONNXModelServer(model_path)
            logger.info(f"Loaded model {key} into registry")
        except Exception as e:
            logger.error(f"Failed to load model {key}: {e}")
            raise

    def set_champion(self, model_name: str, version: str):
        key = f"{model_name}:{version}"
        if key not in self.models:
            raise ValueError(f"Cannot set {key} as champion because it is not loaded.")
        self.champions[model_name] = version
        logger.info(f"Set champion for {model_name} to {version}")

    def get_champion_version(self, model_name: str) -> str:
        return self.champions.get(model_name, "")

    def get_model(self, model_name: str, version: str | None = None) -> ONNXModelServer:
        if not version:
            version = self.get_champion_version(model_name)
            if not version:
                raise ModelInferenceError(f"No champion version set for {model_name}")

        key = f"{model_name}:{version}"
        model = self.models.get(key)
        if not model:
            raise ModelInferenceError(f"Model {key} not found in registry")
        return model

    def predict_with_shadow(
        self, model_name: str, features: np.ndarray, shadow_version: str | None = None
    ) -> tuple[np.ndarray, np.ndarray | None]:

        champion = self.get_model(model_name)
        champ_preds, _ = champion.predict_with_latency(features)

        shadow_preds = None
        if shadow_version:
            try:
                shadow = self.get_model(model_name, shadow_version)
                shadow_preds, _ = shadow.predict_with_latency(features)

                # In production, we'd log the divergence between champ and shadow here.
            except Exception as e:
                logger.warning(f"Shadow inference failed for {model_name}:{shadow_version} - {e}")

        return champ_preds, shadow_preds
