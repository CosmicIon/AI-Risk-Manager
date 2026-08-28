from langchain_core.tools import tool


@tool
def render_template(network: str, reason_code: str, evidence: dict) -> str:
    """Render a fallback chargeback response template.

    Args:
        network: The card network (e.g., VISA, Mastercard).
        reason_code: The chargeback reason code.
        evidence: Dictionary containing evidence details.

    Returns:
        A formatted chargeback representment narrative string.
    """
    return f"""CHARGEBACK REPRESENTMENT

Network: {network}
Reason Code: {reason_code}

TRANSACTION SUMMARY
-------------------
Order ID: {evidence.get("order_id", "Unknown")}
Amount: {evidence.get("total_amount", "Unknown")} {evidence.get("currency", "USD")}
Date: {evidence.get("order_date", "Unknown")}

EVIDENCE PRESENTED
------------------
3DS Authenticated: {evidence.get("3ds_authenticated", False)}
AVS Match: {evidence.get("avs_match", "N")}
Delivery Proof URL: {evidence.get("proof_url", "Not available")}
Signed By: {evidence.get("signed_by", "Not available")}

MERCHANT RESPONSE
-----------------
The customer participated in this transaction as evidenced by AVS and 3DS matching,
and the goods were delivered successfully to the authorized address.

REQUESTED ACTION
----------------
We respectfully request this chargeback be reversed and the funds returned to the merchant.
"""
