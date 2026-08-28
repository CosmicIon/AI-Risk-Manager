import statistics
import time

from src.streaming.app import app

# Table storing a list of (timestamp, amount) tuples
amount_table = app.Table("amount_windows", default=list, partitions=8)


def update_amount_window(
    tenant_id: str, customer_id: str, amount: float, window_seconds: int = 3600
):
    """
    Append an amount to the sliding window and prune old entries.
    """
    key = f"{tenant_id}:{customer_id}"
    now = time.time()

    history = amount_table[key]
    if history is None:
        history = []

    # Prune old entries
    cutoff = now - window_seconds
    history = [(ts, amt) for ts, amt in history if ts >= cutoff]

    # Add new entry
    history.append((now, float(amount)))

    # Update table
    amount_table[key] = history


def get_amount_stats(
    tenant_id: str, customer_id: str, window_seconds: int = 3600
) -> dict[str, float]:
    """
    Compute statistics over the current sliding window.
    """
    key = f"{tenant_id}:{customer_id}"
    history = amount_table[key]

    if not history:
        return {"mean": 0.0, "stddev": 0.0, "p95": 0.0, "count": 0}

    now = time.time()
    cutoff = now - window_seconds
    valid_amounts = [amt for ts, amt in history if ts >= cutoff]

    count = len(valid_amounts)
    if count == 0:
        return {"mean": 0.0, "stddev": 0.0, "p95": 0.0, "count": 0}

    mean = statistics.mean(valid_amounts)
    stddev = statistics.stdev(valid_amounts) if count > 1 else 0.0

    valid_amounts.sort()
    idx = int(0.95 * count)
    if idx >= count:
        idx = count - 1
    p95 = valid_amounts[idx]

    return {"mean": mean, "stddev": stddev, "p95": p95, "count": count}
