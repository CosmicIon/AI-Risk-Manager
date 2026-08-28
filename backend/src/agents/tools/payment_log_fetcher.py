from langchain_core.tools import tool


@tool
def fetch_payment_logs(transaction_id: str, tenant_id: str) -> dict:
    """Fetch 3DS authentication logs, AVS match results, IP geolocation from payment gateway.

    Args:
        transaction_id: The ID of the transaction to look up.
        tenant_id: The tenant ID associated with the transaction.

    Returns:
        Payment logs including 3DS status, AVS match, and IP details.
    """
    if not transaction_id:
        return {"found": False}

    return {
        "found": True,
        "transaction_id": transaction_id,
        "3ds_authenticated": True,
        "avs_match": "Y",  # Y = Match
        "cvv_match": "M",  # M = Match
        "ip_country": "US",
        "ip_city": "Anytown",
        "device_fingerprint_match": True
    }
