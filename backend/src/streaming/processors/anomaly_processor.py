import logging
import uuid
from datetime import UTC, datetime

import numpy as np

from src.core.enums import AlertSeverity, SpikeClassification
from src.core.schemas.fraud_alert import AnomalyAlert
from src.streaming.app import app
from src.streaming.processors.transaction_processor import transactions_topic

logger = logging.getLogger(__name__)

alerts_topic = app.topic("alerts.outbound", value_type=AnomalyAlert)  # type: ignore

segment_counts = app.Table("segment_counts_1m", default=int, partitions=8).tumbling(
    60.0, expires=3600.0
)

baseline_table = app.Table("segment_baselines", default=float, partitions=8)
calendar_events = app.Table("calendar_events", default=list, partitions=1)


# Mocking the ML ensemble for streaming runtime
class MockEnsemble:
    def detect(self, point, seq, tenant):
        return AnomalyAlert(
            alert_id=uuid.uuid4(),
            tenant_id=tenant,
            detected_at=datetime.now(UTC),
            severity=AlertSeverity.WARNING,
            spike_classification=SpikeClassification.UNCERTAIN,
            affected_segment="global",
            baseline_tps=1.0,
            current_tps=5.0,
            deviation_factor=5.0,
            window_seconds=60,
            is_calendar_adjusted=False,
        )


ensemble = MockEnsemble()
ALPHA = 0.1


def check_calendar_event(tenant_id: str) -> bool:
    events = calendar_events[tenant_id]
    if not events:
        return False
    # Mock behavior: assume event is active if registered
    return True


@app.agent(transactions_topic)
async def process_anomalies(stream):
    async for tx in stream:
        # Use ip_address as a proxy for city since city isn't in TransactionRecord
        segment_key = f"{tx.tenant_id}:{tx.mcc}:{tx.ip_address}"

        segment_counts[segment_key] += 1
        try:
            current_count = segment_counts[segment_key].current()
        except Exception:
            current_count = 1

        current_tps = current_count / 60.0

        prev_baseline = baseline_table[segment_key]
        if prev_baseline == 0.0:
            # Initialize baseline to 1.0 TPS to avoid divide by zero
            baseline_table[segment_key] = max(current_tps, 1.0)
            prev_baseline = baseline_table[segment_key]
        else:
            # We decay the baseline slightly towards current TPS
            baseline_table[segment_key] = (ALPHA * current_tps) + ((1 - ALPHA) * prev_baseline)

        baseline_tps = baseline_table[segment_key]
        deviation = current_tps / baseline_tps

        is_adjusted = False
        threshold_multiplier = 1.0
        if check_calendar_event(tx.tenant_id):
            threshold_multiplier = 2.0
            is_adjusted = True

        warn_threshold = 3.0 * threshold_multiplier
        crit_threshold = 10.0 * threshold_multiplier

        if deviation > warn_threshold:
            point_feat = np.array([[current_tps, deviation]])
            seq_feat = np.zeros((1, 10, 2))

            alert = ensemble.detect(point_feat, seq_feat, uuid.UUID(tx.tenant_id))
            if alert:
                alert.affected_segment = segment_key
                alert.baseline_tps = float(baseline_tps)
                alert.current_tps = float(current_tps)
                alert.deviation_factor = float(deviation)
                alert.is_calendar_adjusted = is_adjusted

                if deviation > crit_threshold:
                    alert.severity = AlertSeverity.CRITICAL

                await alerts_topic.send(value=alert)
                logger.warning(f"AnomalyAlert emitted for {segment_key} (dev: {deviation:.2f})")
