import logging

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

class EvidenceRetrievalError(Exception):
    pass

@tool
def lookup_order(order_id: str, tenant_id: str) -> dict:
    """Fetch order details from the database.

    Args:
        order_id: The ID of the order to look up.
        tenant_id: The tenant ID associated with the order.

    Returns:
        Order details including items, amounts, dates, customer info, and shipping address.
    """
    try:
        # Mocking database call for this module since DB might not have all tables
        if not order_id or order_id == "unknown":
            return {"found": False}

        return {
            "found": True,
            "order_id": order_id,
            "items": [{"name": "Premium Laptop", "quantity": 1, "price": 1200.00}],
            "total_amount": 1200.00,
            "currency": "USD",
            "order_date": "2023-10-01T14:30:00Z",
            "customer_info": {
                "name": "Jane Doe",
                "email": "jane.doe@example.com",
                "phone": "+1234567890"
            },
            "shipping_address": {
                "line1": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345",
                "country": "US"
            },
            "communications": [
                {"date": "2023-10-02T10:00:00Z", "type": "email", "content": "Your order has shipped."},
                {"date": "2023-10-04T12:00:00Z", "type": "email", "content": "Delivery confirmation from carrier."}
            ]
        }
    except Exception as e:
        logger.error(f"Error looking up order {order_id}: {e}")
        raise EvidenceRetrievalError(f"Failed to fetch order: {e}") from e
