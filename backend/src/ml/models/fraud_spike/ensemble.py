import uuid
from datetime import UTC, datetime

import numpy as np

from src.core.enums import AlertSeverity, SpikeClassification
from src.core.schemas.fraud_alert import AnomalyAlert


class FraudSpikeEnsemble:
    def __init__(self, iso_forest, lstm_autoencoder, lstm_threshold: float):
        self.iso_forest = iso_forest
        self.lstm = lstm_autoencoder
        self.lstm_threshold = lstm_threshold

    def detect(
        self, point_features: np.ndarray, sequence_features: np.ndarray, tenant_id: uuid.UUID
    ) -> AnomalyAlert | None:
        """
        Runs both models.
        Returns CRITICAL if both agree it's an anomaly.
        Returns WARNING if one agrees.
        Returns None (or INFO) if neither.
        """
        iso_anomaly, iso_score = self.iso_forest.detect(point_features)
        iso_anomaly = bool(iso_anomaly[0])

        lstm_anomaly, lstm_score = self.lstm.detect(sequence_features, self.lstm_threshold)

        if iso_anomaly and lstm_anomaly:
            severity = AlertSeverity.CRITICAL
            spike = SpikeClassification.ATTACK
        elif iso_anomaly or lstm_anomaly:
            severity = AlertSeverity.WARNING
            spike = SpikeClassification.UNCERTAIN
        else:
            return None  # Not an anomaly

        return AnomalyAlert(
            alert_id=uuid.uuid4(),
            tenant_id=tenant_id,
            detected_at=datetime.now(UTC),
            severity=severity,
            spike_classification=spike,
            affected_segment="global",
            baseline_tps=10.0,
            current_tps=50.0,
            deviation_factor=5.0,
            window_seconds=60,
            is_calendar_adjusted=False,
        )
