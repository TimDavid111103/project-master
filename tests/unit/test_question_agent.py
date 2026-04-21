from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents import question_agent
from backend.schemas.agents.question import QuestionAgentInput, QuestionAgentOutput
from backend.schemas.agents.common import ClarifyingQuestion


@pytest.mark.asyncio
async def test_question_agent_returns_structured_output(mock_anthropic_client):
    expected_output = {
        "questions": [
            {
                "question_id": "q1",
                "question_text": "What is the primary goal of this prompt?",
                "rationale": "Surfaces core intent",
            }
        ]
    }
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = expected_output
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(content=[tool_block])
    )

    result = await question_agent.run(
        mock_anthropic_client,
        QuestionAgentInput(original_prompt="Summarize recent ML papers on RAG."),
    )

    assert isinstance(result, QuestionAgentOutput)
    assert len(result.questions) == 1
    assert isinstance(result.questions[0], ClarifyingQuestion)
    assert result.questions[0].question_id == "q1"


@pytest.mark.asyncio
async def test_question_agent_calls_anthropic_with_correct_tool(mock_anthropic_client):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = {"questions": []}
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(content=[tool_block])
    )

    await question_agent.run(
        mock_anthropic_client,
        QuestionAgentInput(original_prompt="test"),
    )

    call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
    assert call_kwargs["tool_choice"] == {"type": "tool", "name": "output_questions"}
    assert any(t["name"] == "output_questions" for t in call_kwargs["tools"])
