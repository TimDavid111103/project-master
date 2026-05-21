import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.schemas.agents.clarifying import ClarifyingAgentOutput
from backend.schemas.agents.common import ClarifyingQuestion

_PROJECT_ID = str(uuid.uuid4())


@pytest.mark.asyncio
async def test_session_start_returns_questions(api_client):
    mock_output = ClarifyingAgentOutput(
        questions=[
            ClarifyingQuestion(
                question_id="q1",
                question_text="What is the primary goal of this prompt?",
                rationale="Surfaces core intent",
            )
        ]
    )

    with (
        patch(
            "backend.api.v1.endpoints.session.run_start_pipeline",
            new=AsyncMock(return_value=mock_output),
        ),
        patch("backend.agents.base.get_anthropic_client", return_value=MagicMock()),
    ):
        response = await api_client.post(
            "/api/v1/session/start",
            json={
                "original_prompt": "How do I build a RAG pipeline?",
                "project_id": _PROJECT_ID,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert "session_context" in data
    assert "questions" in data
    assert data["session_context"]["original_prompt"] == "How do I build a RAG pipeline?"
    assert data["session_context"]["project_id"] == _PROJECT_ID
    assert len(data["questions"]) == 1
    assert data["questions"][0]["question_id"] == "q1"


@pytest.mark.asyncio
async def test_session_start_missing_project_id_returns_422(api_client):
    response = await api_client.post(
        "/api/v1/session/start",
        json={"original_prompt": "How do I build a RAG pipeline?"},
    )
    assert response.status_code == 422
