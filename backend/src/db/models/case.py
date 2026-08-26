import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Index, UniqueConstraint
from sqlalchemy import text as sa_text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from src.db.models.base import Base


class Case(Base):
    __tablename__ = "risk_cases"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("risk_tenants.id", ondelete="CASCADE"), index=True
    )
    source: Mapped[str] = mapped_column(index=True)  # chargeback, return, fraud_alert
    source_id: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column(index=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("risk_users.id", ondelete="SET NULL"), nullable=True
    )
    priority: Mapped[int] = mapped_column(default=0)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution: Mapped[str | None] = mapped_column(nullable=True)
    metadata_data: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        UniqueConstraint("tenant_id", "source", "source_id", name="uq_tenant_source_id"),
        Index(
            "idx_cases_open",
            "tenant_id",
            "deadline",
            postgresql_where=sa_text("status NOT IN ('WON', 'LOST', 'EXPIRED', 'ACCEPTED_LOSS')"),
        ),
    )
