import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.chargeback import ChargebackRecord


class ChargebackRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chargeback(
        self, case_id: uuid.UUID, tenant_id: uuid.UUID, network: str, arn: str,
        reason_code: str, transaction_id: str, transaction_date: datetime,
        transaction_amount: Decimal
    ) -> ChargebackRecord:
        try:
            record = ChargebackRecord(
                case_id=case_id,
                tenant_id=tenant_id,
                network=network,
                arn=arn,
                reason_code=reason_code,
                transaction_id=transaction_id,
                transaction_date=transaction_date,
                transaction_amount=transaction_amount
            )
            self.session.add(record)
            await self.session.commit()
            await self.session.refresh(record)
            return record
        except IntegrityError as e:
            await self.session.rollback()
            raise ValueError(f"Chargeback with ARN {arn} already exists for this tenant.") from e

    async def update_evidence_bundle(self, chargeback_id: uuid.UUID, bundle: dict) -> ChargebackRecord | None:
        stmt = select(ChargebackRecord).where(ChargebackRecord.id == chargeback_id)
        result = await self.session.execute(stmt)
        record = result.scalar_one_or_none()

        if not record:
            return None

        record.evidence_bundle = bundle
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_win_rate_stats(self) -> dict:
        # Implicitly filtered by tenant via RLS
        stmt_total = select(func.count(ChargebackRecord.id)).where(ChargebackRecord.outcome.isnot(None))
        stmt_won = select(func.count(ChargebackRecord.id)).where(ChargebackRecord.outcome == "WON")

        total = await self.session.scalar(stmt_total) or 0
        won = await self.session.scalar(stmt_won) or 0

        rate = (won / total * 100) if total > 0 else 0.0

        return {
            "total_resolved": total,
            "total_won": won,
            "win_rate_percentage": round(rate, 2)
        }
