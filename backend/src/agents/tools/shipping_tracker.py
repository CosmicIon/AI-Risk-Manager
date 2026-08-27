from langchain_core.tools import tool

@tool
def track_shipment(tracking_number: str, carrier: str) -> dict:
    """Mock external shipping API call.
    
    Args:
        tracking_number: The tracking number to track.
        carrier: The shipping carrier (e.g., FedEx, UPS).
        
    Returns:
        Shipping status including delivery date, who signed, and proof URL.
    """
    if not tracking_number:
        return {"delivered": False, "error": "No tracking number provided"}
        
    return {
        "delivered": True,
        "delivery_date": "2023-10-04T14:00:00Z",
        "signed_by": "J. DOE",
        "proof_url": f"https://shipping.provider.com/proof/{tracking_number}",
        "carrier": carrier,
        "tracking_number": tracking_number
    }
