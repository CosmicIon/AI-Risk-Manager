from datetime import timedelta

from src.streaming.app import app

# Tumbling window tables for different time spans
velocity_table_1m = app.Table("velocity_1m", default=int, partitions=8).tumbling(
    60.0, expires=timedelta(hours=1)
)

velocity_table_5m = app.Table("velocity_5m", default=int, partitions=8).tumbling(
    300.0, expires=timedelta(hours=1)
)

velocity_table_1h = app.Table("velocity_1h", default=int, partitions=8).tumbling(
    3600.0, expires=timedelta(hours=24)
)


def get_velocity(tenant_id: str, customer_id: str) -> dict[str, int]:
    """
    Get the velocity counts for the given tenant and customer across windows.
    Returns {"1m": count, "5m": count, "1h": count}
    """
    key = f"{tenant_id}:{customer_id}"

    # In a Faust windowed table, calling .value() gives the current window's value.
    try:
        count_1m = velocity_table_1m[key].current()
    except (KeyError, AttributeError):
        count_1m = 0

    try:
        count_5m = velocity_table_5m[key].current()
    except (KeyError, AttributeError):
        count_5m = 0

    try:
        count_1h = velocity_table_1h[key].current()
    except (KeyError, AttributeError):
        count_1h = 0

    return {
        "1m": count_1m,
        "5m": count_5m,
        "1h": count_1h,
    }
