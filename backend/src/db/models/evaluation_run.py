import uuid
from datetime import datetime
from typing import Any

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from src.db.models.base import Base


class EvaluationRun(Base):
    __tablename__ = "risk_evaluations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    model_name: Mapped[str] = mapped_column(index=True)
    model_version: Mapped[str] = mapped_column()
    holdout_set_version: Mapped[str] = mapped_column()
    holdout_set_hash: Mapped[str] = mapped_column()
    metrics: Mapped[dict[str, Any]] = mapped_column(JSONB)
    threshold: Mapped[float] = mapped_column()
    is_champion: Mapped[bool] = mapped_column(default=False)
    report_url: Mapped[str] = mapped_column()
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
