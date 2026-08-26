import logging
import json
import time
from typing import TypeVar
import asyncio

import google.generativeai as genai
from pydantic import BaseModel
from google.generativeai.types import GenerationConfig
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, InternalServerError

from src.core.exceptions import LLMResponseError

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class GeminiLLMClient:
    def __init__(self, api_key: str):
        genai.configure(api_key=api_key)
        # Using Gemini 1.5 Flash as standard for fast reasoning tasks
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.api_key_configured = bool(api_key and api_key != "mock_key")

    async def _execute_with_retry(self, func, *args, **kwargs):
        """Exponential backoff retry decorator logic."""
        max_retries = 3
        base_delay = 1.0

        for attempt in range(max_retries + 1):
            try:
                start_time = time.perf_counter_ns()
                response = await asyncio.to_thread(func, *args, **kwargs)
                latency_ms = (time.perf_counter_ns() - start_time) / 1_000_000
                
                # Try to extract token counts if available
                input_tokens = 0
                output_tokens = 0
                try:
                    if hasattr(response, 'usage_metadata'):
                        input_tokens = response.usage_metadata.prompt_token_count
                        output_tokens = response.usage_metadata.candidates_token_count
                except Exception:
                    pass

                logger.debug(f"LLM call succeeded in {latency_ms:.2f}ms. Tokens: IN={input_tokens} OUT={output_tokens}")
                return response
            
            except (ResourceExhausted, ServiceUnavailable, InternalServerError) as e:
                if attempt == max_retries:
                    logger.error(f"LLM call failed after {max_retries} retries: {e}")
                    raise
                delay = base_delay * (2 ** attempt)
                logger.warning(f"LLM API error ({type(e).__name__}). Retrying in {delay}s...")
                await asyncio.sleep(delay)
            except Exception as e:
                logger.error(f"Unexpected LLM error: {e}")
                raise

    async def generate_structured(self, prompt: str, response_schema: type[T], temperature: float = 0.2) -> T:
        if not self.api_key_configured:
            logger.warning("Using mocked LLM response for generate_structured due to missing API key")
            raise RuntimeError("API Key not configured. Cannot generate structured response.")

        schema_json = response_schema.model_json_schema()
        
        system_instruction = (
            f"You are a strict data extraction and reasoning engine. "
            f"You MUST return valid JSON matching the following schema: {json.dumps(schema_json)}"
        )
        
        config = GenerationConfig(
            temperature=temperature,
            response_mime_type="application/json",
        )

        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            system_instruction=system_instruction
        )

        response = await self._execute_with_retry(
            model.generate_content,
            prompt,
            generation_config=config
        )

        try:
            return response_schema.model_validate_json(response.text)
        except Exception as e:
            # Correction prompt logic
            logger.warning(f"Failed to parse JSON on first attempt: {e}. Retrying with correction prompt.")
            correction_prompt = f"Your previous response was invalid JSON or mismatched the schema. Error: {str(e)}\n\nOriginal Request:\n{prompt}"
            
            response = await self._execute_with_retry(
                model.generate_content,
                correction_prompt,
                generation_config=config
            )
            try:
                return response_schema.model_validate_json(response.text)
            except Exception as e2:
                raise LLMResponseError(f"Failed to parse structured LLM response after retry: {e2}")

    async def generate_text(self, prompt: str, temperature: float = 0.3, max_tokens: int = 4096) -> str:
        if not self.api_key_configured:
            return "Mocked response text."

        config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        
        response = await self._execute_with_retry(
            self.model.generate_content,
            prompt,
            generation_config=config
        )
        return response.text

    async def health_check(self) -> bool:
        if not self.api_key_configured:
            return True # Mocked environment

        try:
            await self._execute_with_retry(
                self.model.generate_content,
                "ping",
                generation_config=GenerationConfig(max_output_tokens=1)
            )
            return True
        except Exception as e:
            logger.error(f"LLM health check failed: {e}")
            return False
