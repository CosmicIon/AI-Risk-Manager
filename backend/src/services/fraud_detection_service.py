import logging
from datetime import datetime
from uuid import UUID

from src.core.enums import CaseSource
from src.core.schemas.case import CaseCreate
from src.db.models.tenant import Tenant
from src.db.repositories.case_repo import CaseRepository
from src.integrations.kafka_producer import TypedKafkaProducer
from src.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class FraudDetectionService:
    def __init__(
        self,
        case_repo: CaseRepository,
        kafka: TypedKafkaProducer,
        notification_svc: NotificationService,
    ):
        self.case_repo = case_repo
        self.kafka = kafka
        self.notification_svc = notification_svc

    async def handle_alert(self, alert_data: dict, tenant: Tenant, session):
        severity = alert_data.get("severity", "INFO")

        if severity in ["WARNING", "CRITICAL"]:
            case_create = CaseCreate(
                tenant_id=tenant.id,
                source=CaseSource.FRAUD_ALERT,
                source_id=alert_data.get("alert_id", "unknown"),
                priority=10 if severity == "CRITICAL" else 5,
            )
            case = await self.case_repo.create(session, case_create)
            logger.info(f"Created fraud case {case.id} for alert {alert_data.get('alert_id')}")

        # Route alert based on tenant config
        await self.notification_svc.route_alert(alert_data, tenant)

    async def register_event(
        self, tenant_id: UUID, event_name: str, start: datetime, end: datetime
    ):
        # Register a calendar event for the Faust stream processors to adjust anomaly baselines
        event = {
            "event_type": "calendar.registered",
            "tenant_id": str(tenant_id),
            "event_name": event_name,
            "start": start.isoformat(),
            "end": end.isoformat(),
        }
        # In a real system, you might save this to DB/Redis as well.
        await self.kafka.send_event("tenant.config", event)  # type: ignore
        logger.info(f"Registered calendar event {event_name} for tenant {tenant_id}")

    async def get_active_alerts(self, tenant_id: UUID) -> list[dict]:
        # MVP stub
        return []
