import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import DateTime
from sqlalchemy.sql import func

from src.db.models.base import Base

class AuditLog(Base):
    __tablename__ = "risk_audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("risk_tenants.id", ondelete="CASCADE"), index=True)
    case_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("risk_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    actor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("risk_users.id", ondelete="CASCADE"))
    action: Mapped[str] = mapped_column()
    old_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    new_value: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    ip_address: Mapped[str | None] = mapped_column(nullable=True)

    # Note: For production with high volume, this table is partitioned by month on `timestamp` 
    # to meet retention compliance requirements. We will add partitioning setup in Alembic.
