import pytest
from pydantic import BaseModel
from src.integrations.llm_client import GeminiLLMClient

class MockSchema(BaseModel):
    name: str
    age: int

@pytest.mark.asyncio
async def test_llm_client_mocked():
    client = GeminiLLMClient(api_key="mock_key")
    
    assert await client.health_check()
    assert await client.generate_text("hi") == "Mocked response text."
    
    with pytest.raises(RuntimeError):
        await client.generate_structured("hi", MockSchema)
