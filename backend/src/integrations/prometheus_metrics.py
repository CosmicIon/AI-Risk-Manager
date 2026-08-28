from prometheus_client import Counter, Gauge, Histogram

# Histograms for latency
return_scoring_latency_seconds = Histogram(
    "return_scoring_latency_seconds",
    "Return scoring inference latency",
    buckets=[0.01, 0.025, 0.05, 0.1, 0.15, 0.3],
)

chargeback_processing_duration_seconds = Histogram(
    "chargeback_processing_duration_seconds",
    "Chargeback evidence assembly duration",
    buckets=[10, 30, 60, 120, 300],
)

feature_staleness_seconds = Histogram(
    "feature_staleness_seconds", "Feature cache staleness", ["feature_group"]
)

# Counters for totals
requests_total = Counter(
    "requests_total", "Total API requests", ["method", "endpoint", "status_code"]
)

model_inferences_total = Counter(
    "model_inferences_total", "Total model inferences", ["model_name", "model_version"]
)

llm_tokens_total = Counter("llm_tokens_total", "Total LLM tokens used", ["model", "direction"])

rate_limit_hits_total = Counter("rate_limit_hits_total", "Rate limit rejections", ["endpoint"])

# Gauges for current state
active_cases = Gauge("active_cases", "Currently active cases", ["source", "status"])

kafka_consumer_lag = Gauge(
    "kafka_consumer_lag", "Kafka consumer lag by topic", ["topic", "partition"]
)
