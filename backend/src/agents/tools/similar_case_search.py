import logging
from typing import Any

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


@tool
async def search_similar_cases(
    case_summary: str, reason_code: str, network: str, limit: int = 5
) -> list[dict[str, Any]]:
    """Search for similar past chargeback cases that were won.

    Args:
        case_summary: A brief description of the current case.
        reason_code: The chargeback reason code.
        network: The card network (e.g., VISA, Mastercard).
        limit: Maximum number of similar cases to return.

    Returns:
        List of similar past cases with outcomes and winning narratives.
    """
    # In a full production implementation, we would embed the `case_summary`
    # using an embedding model and query Qdrant. For this module, we return mock similar cases.
    logger.info(f"Searching for similar cases: reason_code={reason_code}, network={network}")
    return [
        {
            "case_id": "sim_case_1",
            "outcome": "WON",
            "narrative_summary": "We proved the customer signed for the delivery at the billing address matching AVS.",
            "similarity_score": 0.95,
        },
        {
            "case_id": "sim_case_2",
            "outcome": "WON",
            "narrative_summary": "The 3DS authentication log was sufficient to win the dispute for fraud.",
            "similarity_score": 0.88,
        },
    ]
