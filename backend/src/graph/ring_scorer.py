import uuid
from datetime import datetime, timezone
from src.core.schemas.fraud_alert import AnomalyAlert
from src.core.enums import AlertSeverity, SpikeClassification

def score_ring(community: dict, transaction_stats: dict) -> float:
    """
    Score a community for abuse ring suspicion (0.0 to 1.0).
    Weighted heuristics:
    - address sharing: 0.3
    - device sharing: 0.3
    - timing coordination: 0.2
    - chargeback rate: 0.2
    """
    score = 0.0
    buyers = community.get("buyers", 1)
    
    # Heuristic 1: Address sharing
    addresses = community.get("addresses", buyers)
    if buyers > 1 and addresses < buyers:
        ratio = 1.0 - (addresses / buyers)
        score += 0.3 * min(ratio * 2, 1.0) # e.g. 1 address / 5 buyers -> 1 - 0.2 = 0.8 * 2 = 1.0 -> 0.3
        
    # Heuristic 2: Device sharing
    devices = community.get("devices", buyers)
    if buyers > 1 and devices < buyers:
        ratio = 1.0 - (devices / buyers)
        score += 0.3 * min(ratio * 2, 1.0)
        
    # Heuristic 3: Timing coordination
    timing_score = transaction_stats.get("timing_score", 0.0)
    score += 0.2 * min(timing_score, 1.0)
    
    # Heuristic 4: Chargeback/Return rate
    chargeback_rate = transaction_stats.get("chargeback_rate", 0.0)
    if chargeback_rate > 0.05: # >5% is suspicious
        score += 0.2 * min((chargeback_rate - 0.05) * 10, 1.0)
        
    return min(score, 1.0)


def generate_ring_narrative(community: dict, score: float) -> str:
    """Generate a human-readable explanation of why this cluster is suspicious."""
    buyers = community.get("buyers", 1)
    devices = community.get("devices", buyers)
    addresses = community.get("addresses", buyers)
    
    reasons = []
    if buyers > 1:
        if devices < buyers:
            reasons.append(f"{buyers} distinct buyers are sharing {devices} physical devices.")
        if addresses < buyers:
            reasons.append(f"Shipments are directed to only {addresses} addresses across {buyers} accounts.")
            
    if score > 0.7:
        severity = "High"
    elif score > 0.4:
        severity = "Moderate"
    else:
        severity = "Low"
        
    narrative = f"[{severity} Suspicion Ring] "
    if reasons:
        narrative += "Detected structural anomalies indicating coordinated activity: " + " ".join(reasons)
    else:
        narrative += "Community cluster detected but lacks strong anomaly indicators."
        
    return narrative


def format_for_alert(community: dict, score: float, narrative: str, tenant_id: uuid.UUID) -> AnomalyAlert | None:
    """Create alert if score > 0.7."""
    if score > 0.7:
        return AnomalyAlert(
            alert_id=uuid.uuid4(),
            tenant_id=tenant_id,
            detected_at=datetime.now(timezone.utc),
            severity=AlertSeverity.CRITICAL if score > 0.9 else AlertSeverity.WARNING,
            spike_classification=SpikeClassification.ORGANIC_SPIKE, # Mock value as this is abuse ring
            affected_segment=f"community_{community.get('community_id', 'unknown')}",
            baseline_tps=0.0,
            current_tps=0.0,
            deviation_factor=score,
            window_seconds=86400,
            is_calendar_adjusted=False
        )
    return None
