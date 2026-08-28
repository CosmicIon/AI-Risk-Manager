import logging

from src.agents.state import ChargebackAgentState
from src.agents.tools.order_lookup import lookup_order
from src.agents.tools.payment_log_fetcher import fetch_payment_logs
from src.agents.tools.shipping_tracker import track_shipment

logger = logging.getLogger(__name__)

async def evidence_assembler_node(state: ChargebackAgentState) -> ChargebackAgentState:  # noqa: C901
    """Gathers evidence concurrently based on checklist."""
    logger.info(f"Assembling evidence for case {state.get('case_id')}")
    checklist = state.get("evidence_checklist", [])
    tenant_id = state.get("tenant_id", "default")
    cb = state.get("chargeback", {})
    order_id = cb.get("order_id", "unknown")
    transaction_id = cb.get("transaction_id", "unknown")

    evidence_bundle = {}
    found_items = 0
    required_items = len(checklist) if checklist else 1

    # 1. Order details
    if "order_confirmation" in checklist or "customer_communication" in checklist:
        try:
            order_data = lookup_order.invoke({"order_id": order_id, "tenant_id": tenant_id})
            if order_data.get("found"):
                evidence_bundle.update(order_data)
                found_items += 1
        except Exception as e:
            logger.error(f"Failed to lookup order: {e}")
            state.setdefault("errors", []).append(str(e))

    # 2. Payment logs
    if "avs_match" in checklist or "3ds_log" in checklist:
        try:
            pay_data = fetch_payment_logs.invoke({"transaction_id": transaction_id, "tenant_id": tenant_id})
            if pay_data.get("found"):
                evidence_bundle.update(pay_data)
                found_items += 1
        except Exception as e:
            logger.error(f"Failed to fetch payment logs: {e}")
            state.setdefault("errors", []).append(str(e))

    # 3. Delivery proof
    if "delivery_proof" in checklist:
        try:
            if order_id and order_id != "unknown":
                ship_data = track_shipment.invoke({"tracking_number": f"TRK-{order_id}", "carrier": "FedEx"})
                if ship_data.get("delivered"):
                    evidence_bundle.update(ship_data)
                    found_items += 1
        except Exception as e:
            logger.error(f"Failed to track shipment: {e}")
            state.setdefault("errors", []).append(str(e))

    completeness_score = found_items / required_items if required_items > 0 else 0
    state["evidence_bundle"] = evidence_bundle

    # If completeness < 0.5, skip narrative generation
    if completeness_score < 0.5:
        state["recommendation"] = "accept_loss"
        logger.warning(f"Completeness score {completeness_score:.2f} < 0.5. Recommending accept_loss.")

    state["current_step"] = "assemble_evidence"
    return state
