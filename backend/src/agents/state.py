from typing import Any, TypedDict


class ChargebackAgentState(TypedDict):
    """
    State definition for the Chargeback Agent Workflow in LangGraph.
    """
    case_id: str
    tenant_id: str
    chargeback: dict[str, Any]  # Serialized ChargebackNotification
    reason_code: str
    network: str
    evidence_checklist: list[str]
    evidence_items: list[dict[str, Any]]
    evidence_bundle: dict[str, Any] | None
    narrative_draft: str | None
    win_probability: float | None
    recommendation: str | None
    errors: list[str]
    current_step: str
    trace_id: str
