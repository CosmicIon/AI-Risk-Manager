"""Case management models for analysts and automated systems."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from src.core.enums import CaseSource, CaseStatus


class CaseCreate(BaseModel):
    """Payload to create a new risk case."""
    tenant_id: UUID
    source: CaseSource
    source_id: str
    priority: int = Field(default=0, description="Higher means more urgent")
    metadata: dict[str, Any] = Field(default_factory=dict)


class Case(BaseModel):
    """Core Case entity representing an ongoing risk investigation."""
    case_id: UUID
    tenant_id: UUID
    source: CaseSource
    source_id: str
    status: CaseStatus
    assigned_to: UUID | None = None
    priority: int
    created_at: datetime
    updated_at: datetime
    deadline: datetime | None = None
    resolution: str | None = None
    metadata: dict[str, Any]


class CaseUpdate(BaseModel):
    """Payload to update an existing risk case."""
    status: CaseStatus | None = None
    assigned_to: UUID | None = None
    resolution: str | None = None
    metadata: dict[str, Any] | None = None


class AuditLogEntry(BaseModel):
    """Immutable audit log for compliance and action tracking."""
    entry_id: UUID
    case_id: UUID
    actor_id: UUID
    action: str
    old_value: dict[str, Any] | None = None
    new_value: dict[str, Any] | None = None
    timestamp: datetime
    ip_address: str | None = None
