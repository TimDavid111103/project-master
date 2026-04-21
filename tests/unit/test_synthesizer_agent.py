from unittest.mock import AsyncMock, MagicMock

import pytest

from backend.agents import synthesizer_agent
from backend.schemas.agents.common import UserAnswer
from backend.schemas.agents.reformulation import ReformulatedQuery
from backend.schemas.agents.synthesizer import (
    RetrievedDocument,
    SynthesizerAgentInput,
    SynthesizerAgentOutput,
)


@pytest.mark.asyncio
async def test_synthesizer_agent_returns_structured_output(mock_anthropic_client):
    expected_output = {
        "revised_prompt": "Revised: Summarize ML papers on RAG with focus on retrieval.",
        "analysis": "Added specificity around retrieval focus based on user answers.",
    }
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = expected_output
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(content=[tool_block])
    )

    result = await synthesizer_agent.run(
        mock_anthropic_client,
        SynthesizerAgentInput(
            original_prompt="Summarize ML papers on RAG.",
            reformulated_query=ReformulatedQuery(
                category="rag_patterns",
                concept_tags=["retrieval"],
                query_text="RAG retrieval best practices",
            ),
            retrieved_documents=[
                RetrievedDocument(
                    doc_id="abc123",
                    content="RAG systems benefit from dense retrieval...",
                    similarity_score=0.92,
                )
            ],
            answers=[UserAnswer(question_id="q1", answer_text="Focus on retrieval")],
        ),
    )

    assert isinstance(result, SynthesizerAgentOutput)
    assert result.revised_prompt.startswith("Revised:")
    assert len(result.analysis) > 0


@pytest.mark.asyncio
async def test_synthesizer_agent_includes_retrieved_docs_in_user_message(mock_anthropic_client):
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = {"revised_prompt": "x", "analysis": "y"}
    mock_anthropic_client.messages.create = AsyncMock(
        return_value=MagicMock(content=[tool_block])
    )

    await synthesizer_agent.run(
        mock_anthropic_client,
        SynthesizerAgentInput(
            original_prompt="test",
            reformulated_query=ReformulatedQuery(
                category="cat", concept_tags=[], query_text="q"
            ),
            retrieved_documents=[
                RetrievedDocument(doc_id="1", content="doc content here", similarity_score=0.9)
            ],
            answers=[],
        ),
    )

    call_kwargs = mock_anthropic_client.messages.create.call_args.kwargs
    user_message = call_kwargs["messages"][0]["content"]
    assert "doc content here" in user_message
