import logging
from uuid import UUID

from src.core.enums import CaseStatus
from src.core.schemas.case import CaseUpdate
from src.db.repositories.case_repo import CaseRepository

logger = logging.getLogger(__name__)


class CaseManagementService:
    def __init__(self, case_repo: CaseRepository):
        self.case_repo = case_repo

    async def assign(self, case_id: UUID, tenant_id: UUID, user_id: UUID, actor_id: UUID, session):
        """Assign a case to an analyst."""
        logger.info(f"Assigning case {case_id} to user {user_id} by actor {actor_id}")
        return await self.case_repo.update(
            session, case_id, tenant_id, CaseUpdate(assigned_to=user_id)
        )

    async def update_status(
        self,
        case_id: UUID,
        tenant_id: UUID,
        new_status: CaseStatus,
        actor_id: UUID,
        session,
        resolution: str | None = None,
    ):
        """Update case status with basic state machine validation."""
        logger.info(f"Actor {actor_id} updating case {case_id} status to {new_status}")
        case = await self.case_repo.get_by_id(session, case_id, tenant_id)
        if not case:
            raise ValueError(f"Case {case_id} not found")

        # Basic state machine validation
        terminal_states = [
            CaseStatus.WON,
            CaseStatus.LOST,
            CaseStatus.ACCEPTED_LOSS,
            CaseStatus.EXPIRED,
        ]
        if case.status in terminal_states and new_status not in terminal_states:
            raise ValueError(f"Cannot transition from terminal state {case.status} to {new_status}")

        update_data = CaseUpdate(status=new_status)
        if resolution:
            update_data.resolution = resolution

        return await self.case_repo.update(session, case_id, tenant_id, update_data)

    async def get_dashboard_stats(self, tenant_id: UUID, session) -> dict:
        """Aggregate stats for the dashboard."""
        # Call the existing get_stats method from CaseRepository
        return await self.case_repo.get_stats(session, tenant_id)

    async def search(
        self, tenant_id: UUID, query: str, filters: dict, page: int, size: int, session
    ):
        """Search and filter cases."""
        # Simple pagination mapping to list for MVP
        skip = (page - 1) * size
        cases = await self.case_repo.list(session, tenant_id, skip=skip, limit=size)
        # Note: in a real implementation we'd return a total count as well.
        return cases, len(cases)
