from typing import TypedDict, Optional, Any, Dict, List
import uuid

class ChargebackAgentState(TypedDict):
    """
    State definition for the Chargeback Agent Workflow in LangGraph.
    """
    case_id: str
    tenant_id: str
    chargeback: Dict[str, Any]  # Serialized ChargebackNotification
    reason_code: str
    network: str
    evidence_checklist: List[str]
    evidence_items: List[Dict[str, Any]]
    evidence_bundle: Optional[Dict[str, Any]]
    narrative_draft: Optional[str]
    win_probability: Optional[float]
    recommendation: Optional[str]
    errors: List[str]
    current_step: str
    trace_id: str
