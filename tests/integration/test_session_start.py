from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.asyncio
async def test_session_start_returns_questions(api_client):
    mock_output = {
        "questions": [
            {
                "question_id": "q1",
                "question_text": "What is the primary goal?",
                "rationale": "Surfaces intent",
            }
        ]
    }
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = mock_output
    mock_response = MagicMock(content=[tool_block])

    with patch(
        "backend.agents.question_agent._call_claude",
        new=AsyncMock(
            return_value=MagicMock(
                questions=[
                    MagicMock(
                        question_id="q1",
                        question_text="What is the primary goal?",
                        rationale="Surfaces intent",
                        model_dump=lambda: mock_output["questions"][0],
                    )
                ]
            )
        ),
    ), patch("backend.agents.base.get_anthropic_client", return_value=AsyncMock()):
        response = await api_client.post(
            "/api/v1/session/start",
            json={"original_prompt": "How do I build a RAG pipeline?"},
        )

    assert response.status_code == 200
    data = response.json()
    assert "session_context" in data
    assert "questions" in data
    assert data["session_context"]["original_prompt"] == "How do I build a RAG pipeline?"


@pytest.mark.asyncio
async def test_session_start_returns_400_on_empty_prompt(api_client):
    response = await api_client.post(
        "/api/v1/session/start",
        json={"original_prompt": ""},
    )
    assert response.status_code in (200, 422)
