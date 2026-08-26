import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import DateTime, Numeric
from sqlalchemy.sql import func

from src.db.models.base import Base

class ChargebackRecord(Base):
    __tablename__ = "risk_chargebacks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    case_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("risk_cases.id", ondelete="CASCADE"), index=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("risk_tenants.id", ondelete="CASCADE"), index=True)
    network: Mapped[str] = mapped_column()
    arn: Mapped[str] = mapped_column()
    reason_code: Mapped[str] = mapped_column()
    transaction_id: Mapped[str] = mapped_column()
    transaction_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    transaction_amount: Mapped[Decimal] = mapped_column(Numeric)
    evidence_bundle: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    representment_draft: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    win_probability: Mapped[float | None] = mapped_column(nullable=True)
    outcome: Mapped[str | None] = mapped_column(nullable=True)  # won, lost
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_tenant_arn", "tenant_id", "arn", unique=True),
    )
