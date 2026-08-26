import logging
from typing import Any

from langfuse import Langfuse

from src.config import settings

logger = logging.getLogger(__name__)

class LangfuseTracer:
    def __init__(self, public_key: str, secret_key: str, host: str):
        self.enabled = bool(public_key and secret_key and public_key != "mock_public_key")
        if self.enabled:
            self.client = Langfuse(
                public_key=public_key,
                secret_key=secret_key,
                host=host
            )
        else:
            self.client = None

    def create_trace(self, case_id: str, name: str) -> Any | None:
        if not self.enabled or not self.client:
            return None
        return self.client.trace(name=name, metadata={"case_id": case_id})

    def create_span(self, trace: Any | None, name: str, input_data: dict[str, Any], output_data: dict[str, Any] | None = None) -> Any | None:
        if not self.enabled or not trace:
            return None
        span = trace.span(name=name, input=input_data)
        if output_data is not None:
            span.end(output=output_data)
        return span

    def create_generation(self, trace: Any | None, name: str, prompt: str, completion: str, model: str, tokens: dict[str, int] | None = None):
        if not self.enabled or not trace:
            return
        
        usage = None
        if tokens:
            usage = {
                "promptTokens": tokens.get("input", 0),
                "completionTokens": tokens.get("output", 0),
                "totalTokens": tokens.get("input", 0) + tokens.get("output", 0)
            }
            
        trace.generation(
            name=name,
            model=model,
            prompt=prompt,
            completion=completion,
            usage=usage
        )

    def score_trace(self, trace: Any | None, name: str, value: float, comment: str | None = None):
        if not self.enabled or not trace:
            return
        trace.score(
            name=name,
            value=value,
            comment=comment
        )

    def flush(self):
        if self.enabled and self.client:
            self.client.flush()
