import logging

from src.agents.prompts.representment_narrative import narrative_prompt_template
from src.agents.state import ChargebackAgentState
from src.agents.tools import sanitize_input
from src.agents.tools.similar_case_search import search_similar_cases
from src.agents.tools.template_renderer import render_template
from src.config import settings
from src.integrations.llm_client import GeminiLLMClient

logger = logging.getLogger(__name__)

llm_client = GeminiLLMClient(api_key=settings.GEMINI_API_KEY.get_secret_value())


async def narrative_generator_node(state: ChargebackAgentState) -> ChargebackAgentState:
    logger.info(f"Generating narrative for case {state.get('case_id')}")

    # Sanitize potentially unsafe customer input fields if they exist in the chargeback payload
    # In a real app we'd deep sanitize, but for demonstration we sanitize the dispute description
    cb = state.get("chargeback", {})
    desc = cb.get("description", "")
    safe_desc = sanitize_input(desc)

    # 1. Fetch similar cases
    try:
        similar_cases = await search_similar_cases.ainvoke(
            {
                "case_summary": f"Chargeback dispute: {safe_desc}",
                "reason_code": state["reason_code"],
                "network": state["network"],
            }
        )
    except Exception as e:
        logger.error(f"Failed to fetch similar cases: {e}")
        similar_cases = []

    # 2. Build prompt
    prompt = narrative_prompt_template.format(
        network=state["network"],
        reason_code=state["reason_code"],
        evidence=str(state.get("evidence_bundle", {})),
        similar_cases=str(similar_cases),
    )

    # 3. Call LLM
    try:
        draft = await llm_client.generate_text(prompt, max_tokens=1024, temperature=0.2)

        # 4. Basic validation (check for sections)
        if "TRANSACTION SUMMARY" not in draft:
            raise ValueError("LLM output missing required sections")

        state["narrative_draft"] = draft
    except Exception as e:
        logger.error(f"LLM generation failed, falling back to template: {e}")
        state.setdefault("errors", []).append(f"LLM Error: {e}")
        # 5. Fallback to template
        draft = render_template.invoke(
            {
                "network": state["network"],
                "reason_code": state["reason_code"],
                "evidence": state.get("evidence_bundle", {}),
            }
        )
        state["narrative_draft"] = draft

    state["current_step"] = "generate_narrative"
    return state
