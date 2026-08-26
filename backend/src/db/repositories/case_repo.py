import uuid
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.audit_log import AuditLog
from src.db.models.case import Case


class CaseRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_case(
        self, tenant_id: uuid.UUID, source: str, source_id: str,
        status: str, metadata_data: dict, priority: int = 0, deadline: datetime | None = None
    ) -> Case:
        try:
            new_case = Case(
                tenant_id=tenant_id,
                source=source,
                source_id=source_id,
                status=status,
                metadata_data=metadata_data,
                priority=priority,
                deadline=deadline
            )
            self.session.add(new_case)
            await self.session.commit()
            await self.session.refresh(new_case)
            return new_case
        except IntegrityError as e:
            await self.session.rollback()
            raise ValueError(f"Case with source {source} and source_id {source_id} already exists.") from e

    async def update_case_status(
        self, case_id: uuid.UUID, new_status: str, actor_id: uuid.UUID, tenant_id: uuid.UUID
    ) -> Case | None:
        stmt = select(Case).where(Case.id == case_id)
        result = await self.session.execute(stmt)
        case = result.scalar_one_or_none()

        if not case:
            return None

        old_status = case.status
        case.status = new_status

        # Create audit log
        audit = AuditLog(
            tenant_id=tenant_id,
            case_id=case.id,
            actor_id=actor_id,
            action="STATUS_CHANGE",
            old_value={"status": old_status},
            new_value={"status": new_status}
        )
        self.session.add(audit)

        await self.session.commit()
        await self.session.refresh(case)
        return case

    async def get_open_cases_past_deadline(self) -> list[Case]:
        # Due to Postgres RLS, this will implicitly be filtered by tenant_id
        # when using a session from get_db_session_with_tenant()
        now = datetime.now(UTC)
        stmt = select(Case).where(
            Case.status.notin_(["WON", "LOST", "EXPIRED", "ACCEPTED_LOSS"]),
            Case.deadline < now
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
