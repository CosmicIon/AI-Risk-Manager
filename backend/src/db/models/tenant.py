import uuid
from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import Numeric, DateTime
from sqlalchemy.sql import func

from src.db.models.base import Base

class Tenant(Base):
    __tablename__ = "risk_tenants"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column()
    api_key_hash: Mapped[str] = mapped_column()
    fp_cost_per_unit: Mapped[Decimal] = mapped_column(Numeric, default=Decimal("500.0"))
    fn_cost_per_unit: Mapped[Decimal] = mapped_column(Numeric, default=Decimal("2000.0"))
    policy_config: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    is_active: Mapped[bool] = mapped_column(default=True)
