from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents import reformulation_agent
from backend.schemas.agents.common import ClarifyingQuestion, UserAnswer
from backend.schemas.agents.reformulation import (
    ReformulationAgentInput,
    ReformulationAgentOutput,
    ReformulatedQuery,
)

_TAXONOMY = {"rag_patterns": ["chunking", "retrieval", "reranking"]}


@pytest.mark.asyncio
async def test_reformulation_agent_returns_structured_output(mock_anthropic_client):
    expected_output = {
        "reformulated_query": {
            "category": "rag_patterns",
            "concept_tags": ["chunking", "retrieval"],
            "query_text": "Best practices for chunking documents in RAG pipelines",
        }
    }
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = expected_output
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(content=[tool_block])
    )

    result = await reformulation_agent.run(
        mock_anthropic_client,
        ReformulationAgentInput(
            original_prompt="How do I chunk documents?",
            questions=[
                ClarifyingQuestion(
                    question_id="q1",
                    question_text="What size documents?",
                    rationale="Affects chunking strategy",
                )
            ],
            answers=[UserAnswer(question_id="q1", answer_text="Large PDFs")],
            taxonomy=_TAXONOMY,
        ),
    )

    assert isinstance(result, ReformulationAgentOutput)
    assert isinstance(result.reformulated_query, ReformulatedQuery)
    assert result.reformulated_query.category == "rag_patterns"


@pytest.mark.asyncio
async def test_reformulation_agent_injects_taxonomy_into_system_prompt(mock_anthropic_client):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = {
        "reformulated_query": {"category": "rag_patterns", "concept_tags": [], "query_text": "test"}
    }
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(content=[tool_block])
    )

    await reformulation_agent.run(
        mock_anthropic_client,
        ReformulationAgentInput(
            original_prompt="test",
            questions=[],
            answers=[],
            taxonomy=_TAXONOMY,
        ),
    )

    call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
    assert "rag_patterns" in call_kwargs["system"]
