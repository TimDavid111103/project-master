import os
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio

# Provide required env vars before any backend module is imported
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-anthropic-key")
os.environ.setdefault("OPENAI_API_KEY", "test-openai-key")
os.environ.setdefault("LANGFUSE_PUBLIC_KEY", "test-lf-public")
os.environ.setdefault("LANGFUSE_SECRET_KEY", "test-lf-secret")


@pytest.fixture
def mock_anthropic_client():
    return AsyncMock()


def make_tool_use_response(data: dict) -> MagicMock:
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = data
    response = MagicMock()
    response.content = [tool_block]
    return response


@pytest_asyncio.fixture
async def api_client():
    from httpx import ASGITransport, AsyncClient
    from backend.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client
