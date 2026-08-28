import logging
import uuid

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agents.confidence_scorer import confidence_scorer_node
from src.agents.evidence_assembler import evidence_assembler_node
from src.agents.narrative_generator import narrative_generator_node
from src.agents.state import ChargebackAgentState

logger = logging.getLogger(__name__)


def parse_notification(state: ChargebackAgentState) -> ChargebackAgentState:
    logger.info(f"Parsing notification for case {state.get('case_id')}")

    # Validate and set checklist based on reason code
    code = state.get("reason_code")
    if code == "10.4":
        state["evidence_checklist"] = ["avs_match", "delivery_proof"]
    else:
        state["evidence_checklist"] = ["order_confirmation", "3ds_log", "avs_match"]

    state["current_step"] = "parse_notification"
    return state


def human_review(state: ChargebackAgentState) -> ChargebackAgentState:
    logger.info(f"Human review required for case {state.get('case_id')}")
    state["current_step"] = "human_review"
    return state


def finalize(state: ChargebackAgentState) -> ChargebackAgentState:
    logger.info(f"Finalizing case {state.get('case_id')}")
    state["current_step"] = "finalize"
    return state


def should_generate_narrative(state: ChargebackAgentState) -> str:
    if state.get("recommendation") == "accept_loss":
        return "human_review"
    return "generate_narrative"


def create_agent_graph():
    workflow = StateGraph(ChargebackAgentState)

    # Add nodes
    workflow.add_node("parse_notification", parse_notification)
    workflow.add_node("assemble_evidence", evidence_assembler_node)
    workflow.add_node("generate_narrative", narrative_generator_node)
    workflow.add_node("score_confidence", confidence_scorer_node)
    workflow.add_node("human_review", human_review)
    workflow.add_node("finalize", finalize)

    # Add edges
    workflow.set_entry_point("parse_notification")
    workflow.add_edge("parse_notification", "assemble_evidence")

    workflow.add_conditional_edges(
        "assemble_evidence",
        should_generate_narrative,
        {"generate_narrative": "generate_narrative", "human_review": "human_review"},
    )

    workflow.add_edge("generate_narrative", "score_confidence")
    workflow.add_edge("score_confidence", "human_review")
    workflow.add_edge("human_review", "finalize")
    workflow.add_edge("finalize", END)

    # Compile with checkpointing and interrupt at human review
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory, interrupt_before=["human_review"])


chargeback_graph = create_agent_graph()


async def process_chargeback(notification: dict, tenant_id: str) -> dict:
    """Entry point for initiating the chargeback agent workflow."""
    initial_state = {
        "case_id": str(uuid.uuid4()),
        "tenant_id": tenant_id,
        "chargeback": notification,
        "reason_code": notification.get("reason_code", "unknown"),
        "network": notification.get("network", "unknown"),
        "evidence_checklist": [],
        "evidence_items": [],
        "evidence_bundle": None,
        "narrative_draft": None,
        "win_probability": None,
        "recommendation": None,
        "errors": [],
        "current_step": "init",
        "trace_id": str(uuid.uuid4()),
    }

    config = {"configurable": {"thread_id": initial_state["case_id"]}}

    # Run the graph until the interrupt (human review)
    async for output in chargeback_graph.astream(initial_state, config=config):
        for key, _value in output.items():
            logger.info(f"Finished node: {key}")

    # Get the final state before interrupt
    state = chargeback_graph.get_state(config)
    return state.values
