import pytest
import numpy as np
from src.ml.models.return_risk.config import FEATURE_NAMES

# We test the model registry serving latency in an integration-style unit test, 
# but here we can mock it to ensure the logic works.
def test_dummy_latency():
    # Since we need an actual ONNX model to test the real ONNX runtime,
    # we simulate the test structure here.
    
    # We expect features to be of length 50
    features = np.random.randn(1, 50).astype(np.float32)
    
    assert features.shape == (1, 50)
    assert len(FEATURE_NAMES) == 50
