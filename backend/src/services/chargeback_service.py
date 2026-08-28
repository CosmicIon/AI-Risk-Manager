import logging
from datetime import UTC, datetime
from uuid import UUID

from src.agents.orchestrator import process_chargeback
from src.core.enums import CaseSource, CaseStatus
from src.core.events import ChargebackEvent
from src.core.schemas.case import CaseCreate, CaseUpdate
from src.core.schemas.chargeback import (
    ChargebackIngestRequest,
    ChargebackIngestResponse,
    ChargebackNotification,
)
from src.db.models.chargeback import ChargebackRecord
from src.db.models.tenant import Tenant
from src.db.repositories.case_repo import CaseRepository
from src.db.repositories.chargeback_repo import ChargebackRepository
from src.integrations.kafka_producer import TypedKafkaProducer

logger = logging.getLogger(__name__)


class ChargebackService:
    def __init__(
        self,
        case_repo: CaseRepository,
        chargeback_repo: ChargebackRepository,
        kafka: TypedKafkaProducer,
    ):
        self.case_repo = case_repo
        self.chargeback_repo = chargeback_repo
        self.kafka = kafka

    async def ingest(
        self, request: ChargebackIngestRequest, tenant: Tenant, session
    ) -> ChargebackIngestResponse:
        logger.info(f"Ingesting chargeback payload for tenant {tenant.id}")

        # 1. Parse raw payload into ChargebackNotification
        # We manually inject tenant_id and default fields required by the model
        payload = request.raw_payload.copy()
        payload["tenant_id"] = str(tenant.id)
        if "received_at" not in payload:
            payload["received_at"] = datetime.now(UTC).isoformat()

        notification = ChargebackNotification.model_validate(payload)

        # 2. Create Case record
        case_create = CaseCreate(
            tenant_id=tenant.id,
            source=CaseSource.CHARGEBACK,
            source_id=notification.arn,
            priority=5,
        )
        case = await self.case_repo.create(session, case_create)

        # 3. Create ChargebackRecord
        record = ChargebackRecord(
            case_id=case.id,
            tenant_id=tenant.id,
            network=notification.network.value,
            arn=notification.arn,
            reason_code=notification.reason_code.value,
            transaction_id=notification.transaction_id,
            transaction_date=notification.transaction_date,
            transaction_amount=notification.transaction_amount,
        )
        await self.chargeback_repo.create(session, record)

        # 4. Emit event
        event = ChargebackEvent(event_type="chargeback.received", **notification.model_dump())
        await self.kafka.send_event("chargebacks.incoming", event)

        # Note: we skip celery enqueue in this MVP and just rely on background tasks in FastAPI controller

        return ChargebackIngestResponse(
            case_id=case.id,
            status=CaseStatus.NEW,
            deadline=notification.deadline,  # type: ignore
            message="Chargeback ingested successfully",
        )

    async def process(self, case_id: UUID, tenant_id: UUID, notification_dict: dict, session):
        """Runs the LangGraph agent pipeline and updates the case status."""
        logger.info(f"Starting agent pipeline for case {case_id}")
        await self.case_repo.update(
            session, case_id, tenant_id, CaseUpdate(status=CaseStatus.EVIDENCE_GATHERING)
        )

        try:
            # 1. Run agent
            final_state = await process_chargeback(notification_dict, str(tenant_id))

            # 2. Update DB with evidence and draft
            evidence_bundle = final_state.get("evidence_bundle") or {}
            draft = final_state.get("narrative_draft")
            win_prob = final_state.get("win_probability")

            await self.chargeback_repo.update_evidence(session, case_id, evidence_bundle)
            if draft:
                record = await self.chargeback_repo.get_by_arn(
                    session, tenant_id, notification_dict["arn"]
                )
                if record:
                    record.representment_draft = draft
                    record.win_probability = win_prob

            # 3. Update case status based on recommendation
            recommendation = final_state.get("recommendation")
            if recommendation == "accept_loss":
                await self.case_repo.update(
                    session, case_id, tenant_id, CaseUpdate(status=CaseStatus.ACCEPTED_LOSS)
                )
            else:
                await self.case_repo.update(
                    session, case_id, tenant_id, CaseUpdate(status=CaseStatus.DRAFT_READY)
                )

        except Exception as e:
            logger.error(f"Agent pipeline failed for case {case_id}: {e}")
            await self.case_repo.update(
                session, case_id, tenant_id, CaseUpdate(status=CaseStatus.NEW)
            )
            raise

    async def review(
        self, case_id: UUID, tenant_id: UUID, action: str, edits: dict, actor_id: UUID, session
    ):
        logger.info(f"Analyst {actor_id} reviewing case {case_id} with action {action}")
        if action == "approve":
            await self.case_repo.update(
                session, case_id, tenant_id, CaseUpdate(status=CaseStatus.SUBMITTED)
            )
        elif action == "edit":
            await self.case_repo.update(
                session, case_id, tenant_id, CaseUpdate(status=CaseStatus.DRAFT_READY)
            )
        elif action == "reject":
            await self.case_repo.update(
                session,
                case_id,
                tenant_id,
                CaseUpdate(status=CaseStatus.ACCEPTED_LOSS, resolution="Rejected by analyst"),
            )
        else:
            raise ValueError(f"Invalid review action: {action}")

    async def get_pending_reviews(self, tenant_id: UUID) -> list[dict]:
        # MVP stub
        return []
