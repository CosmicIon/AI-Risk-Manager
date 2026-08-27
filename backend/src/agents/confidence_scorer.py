import logging
from src.agents.state import ChargebackAgentState

logger = logging.getLogger(__name__)

async def confidence_scorer_node(state: ChargebackAgentState) -> ChargebackAgentState:
    logger.info(f"Scoring confidence for case {state.get('case_id')}")
    
    # In a full implementation, we'd extract features using chargeback_win/features.py
    # and run inference via model_registry.get_model("chargeback_win").
    # We will mock the ML scoring logic based on evidence bundle.
    
    bundle = state.get("evidence_bundle", {})
    score = 0.0
    
    if bundle.get("delivered"):
        score += 0.4
    if bundle.get("3ds_authenticated"):
        score += 0.4
    if bundle.get("avs_match") == "Y":
        score += 0.2
        
    state["win_probability"] = score
    
    # Override recommendation only if we have high confidence.
    # Note: If it's already accept_loss, this might upgrade it, or we could keep it.
    if score > 0.6:
        state["recommendation"] = "respond"
    else:
        state["recommendation"] = "accept_loss"
        
    state["current_step"] = "score_confidence"
    return state
