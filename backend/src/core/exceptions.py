"""Domain exceptions for AI Risk Manager."""

class RiskManagerError(Exception):
    """Base exception for all AI Risk Manager domain errors."""
    def __init__(self, message: str, error_code: str):
        super().__init__(message)
        self.message = message
        self.error_code = error_code


class SchemaValidationError(RiskManagerError):
    """Raised on Pydantic validation failures at service boundaries."""
    def __init__(self, message: str):
        super().__init__(message, "SCHEMA_VALIDATION_ERROR")


class CaseNotFoundError(RiskManagerError):
    """Raised when case ID lookup fails."""
    def __init__(self, case_id: str):
        super().__init__(f"Case with ID {case_id} not found", "CASE_NOT_FOUND")


class DuplicateIngestionError(RiskManagerError):
    """Raised on duplicate chargeback or return ingestion (idempotency violation)."""
    def __init__(self, source_id: str):
        super().__init__(f"Duplicate ingestion for source ID {source_id}", "DUPLICATE_INGESTION")


class ModelInferenceError(RiskManagerError):
    """Raised when ONNX Runtime inference or ML prediction fails."""
    def __init__(self, message: str):
        super().__init__(message, "MODEL_INFERENCE_ERROR")


class EvidenceRetrievalError(RiskManagerError):
    """Raised when an agent tool fails to fetch evidence."""
    def __init__(self, source: str, message: str):
        super().__init__(f"Failed to retrieve evidence from {source}: {message}", "EVIDENCE_RETRIEVAL_ERROR")


class LLMResponseError(RiskManagerError):
    """Raised when LLM returns malformed/unparseable output."""
    def __init__(self, message: str):
        super().__init__(message, "LLM_RESPONSE_ERROR")


class FeatureStoreUnavailableError(RiskManagerError):
    """Raised when Redis feature cache is unreachable."""
    def __init__(self, message: str = "Feature store is unavailable"):
        super().__init__(message, "FEATURE_STORE_UNAVAILABLE")


class DeadlineExceededError(RiskManagerError):
    """Raised when chargeback representment deadline has passed."""
    def __init__(self, case_id: str, deadline: str):
        super().__init__(f"Deadline {deadline} exceeded for case {case_id}", "DEADLINE_EXCEEDED")
