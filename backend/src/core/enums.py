"""Domain enumerations for AI Risk Manager."""

from enum import StrEnum


class CardNetwork(StrEnum):
    """Supported card networks."""

    VISA = "VISA"
    MASTERCARD = "MASTERCARD"
    RUPAY = "RUPAY"
    AMEX = "AMEX"


class ReasonCode(StrEnum):
    """Chargeback reason codes mapped to internal constants."""

    # Visa codes
    FRAUD_CARD_NOT_PRESENT = "10.4"
    MERCHANDISE_NOT_RECEIVED = "13.1"
    NOT_AS_DESCRIBED = "13.3"
    DUPLICATE_PROCESSING = "12.2"
    CANCELLED_RECURRING = "13.7"

    # Mastercard codes (mapping equivalent internal representation if needed,
    # but keeping raw values for direct network compliance)
    UNAUTHORIZED_TRANSACTION = "4837"
    CARDHOLDER_DISPUTE = "4853"

    @classmethod
    def from_network_code(cls, network: CardNetwork, raw_code: str) -> "ReasonCode":
        """Map raw network reason codes to our internal ReasonCode enum."""
        # Normalize and map. For now, assuming raw_code matches the enum values directly.
        # In a real system, there would be a more complex mapping dictionary.
        try:
            return cls(str(raw_code).strip())
        except ValueError:
            # Fallback or generic code could be returned here
            raise ValueError(
                f"Unknown reason code '{raw_code}' for network {network.value}"
            ) from None


class RiskTier(StrEnum):
    """Categorized risk levels for transactions and returns."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CaseStatus(StrEnum):
    """Lifecycle states of a risk/chargeback case."""

    NEW = "NEW"
    EVIDENCE_GATHERING = "EVIDENCE_GATHERING"
    DRAFT_READY = "DRAFT_READY"
    IN_REVIEW = "IN_REVIEW"
    APPROVED = "APPROVED"
    SUBMITTED = "SUBMITTED"
    WON = "WON"
    LOST = "LOST"
    EXPIRED = "EXPIRED"
    ACCEPTED_LOSS = "ACCEPTED_LOSS"


class CaseSource(StrEnum):
    """Origin of a case creation."""

    CHARGEBACK = "CHARGEBACK"
    RETURN = "RETURN"
    FRAUD_ALERT = "FRAUD_ALERT"
    ABUSE_RING = "ABUSE_RING"


class SpikeClassification(StrEnum):
    """Classification of detected velocity anomalies."""

    ORGANIC_SPIKE = "ORGANIC_SPIKE"
    ATTACK = "ATTACK"
    UNCERTAIN = "UNCERTAIN"


class AlertSeverity(StrEnum):
    """Severity levels for system and fraud alerts."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    EMERGENCY = "EMERGENCY"


class NotificationChannel(StrEnum):
    """Supported channels for alert dispatch."""

    EMAIL = "EMAIL"
    SLACK = "SLACK"
    PAGERDUTY = "PAGERDUTY"
    SMS = "SMS"
