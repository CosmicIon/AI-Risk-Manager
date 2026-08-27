import pytest
import numpy as np
import uuid
from src.ml.models.fraud_spike.isolation_forest import IsolationForestDetector
from src.ml.models.fraud_spike.lstm_autoencoder import LSTMAutoencoder
from src.ml.models.fraud_spike.ensemble import FraudSpikeEnsemble
from src.core.enums import AlertSeverity, SpikeClassification

def test_fraud_spike_ensemble():
    iso = IsolationForestDetector()
    lstm = LSTMAutoencoder(input_dim=10, hidden_dim=5)
    
    # Mock detect methods
    iso.detect = lambda x: ([True], [0.5])
    lstm.detect = lambda x, t: (True, 0.8)
    
    ensemble = FraudSpikeEnsemble(iso, lstm, 0.5)
    tenant_id = uuid.uuid4()
    
    alert = ensemble.detect(np.random.randn(1, 10), np.random.randn(1, 10, 10), tenant_id)
    
    assert alert is not None
    assert alert.severity == AlertSeverity.CRITICAL
    assert alert.spike_classification == SpikeClassification.ATTACK
    
    # Test WARNING
    iso.detect = lambda x: ([False], [0.5])
    alert = ensemble.detect(np.random.randn(1, 10), np.random.randn(1, 10, 10), tenant_id)
    assert alert is not None
    assert alert.severity == AlertSeverity.WARNING
    
    # Test None
    lstm.detect = lambda x, t: (False, 0.1)
    alert = ensemble.detect(np.random.randn(1, 10), np.random.randn(1, 10, 10), tenant_id)
    assert alert is None
