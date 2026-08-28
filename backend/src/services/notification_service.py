import logging
from enum import StrEnum

from src.core.schemas.case import Case
from src.db.models.tenant import Tenant

logger = logging.getLogger(__name__)

class NotificationChannel(StrEnum):
    EMAIL = "email"
    SLACK = "slack"
    PAGERDUTY = "pagerduty"
    SMS = "sms"

class NotificationService:
    async def send(self, channel: NotificationChannel, recipient: str, subject: str, body: str, metadata: dict | None = None):
        """Mock notification dispatcher."""
        if channel in [NotificationChannel.EMAIL, NotificationChannel.SLACK]:
            logger.info(f"DISPATCH [{channel} to {recipient}]: {subject} - {body}")
        else:
            logger.warning(f"Notification channel {channel} not fully implemented yet in MVP.")

    async def route_alert(self, alert: dict, tenant: Tenant):
        """Looks up tenant config and sends alerts based on severity."""
        severity = alert.get("severity", "INFO")

        # In a real app, this comes from tenant.notification_config
        # We mock the config routing here:
        mock_config = {
            "CRITICAL": [(NotificationChannel.PAGERDUTY, "pd-key-123"), (NotificationChannel.SLACK, "#alerts-critical")],
            "WARNING": [(NotificationChannel.SLACK, "#alerts-warning")],
            "INFO": [(NotificationChannel.EMAIL, "analysts@merchant.com")]
        }

        routes = mock_config.get(severity, [])
        for channel, recipient in routes:
            await self.send(
                channel=channel,
                recipient=recipient,
                subject=f"[{severity}] Anomaly Detected: {alert.get('anomaly_type')}",
                body=f"Score: {alert.get('anomaly_score')}. Details: {alert}",
                metadata=alert
            )

    async def send_deadline_warning(self, case: Case, hours_remaining: int):
        """Send a warning about approaching chargeback deadlines."""
        # Hardcoded to Slack for MVP demo
        await self.send(
            channel=NotificationChannel.SLACK,
            recipient="#chargeback-alerts",
            subject=f"Deadline Approaching: Case {case.case_id}",
            body=f"Case {case.case_id} has a network deadline in {hours_remaining} hours. Please review immediately."
        )
