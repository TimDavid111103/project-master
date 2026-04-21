from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.schemas.agents.common import ClarifyingQuestion


_SESSION_CONTEXT = {
    "original_prompt": "How do I chunk documents for RAG?",
    "questions": [
        {
            "question_id": "q1",
            "question_text": "What document types?",
            "rationale": "Affects chunking strategy",
        }
    ],
}

_ANSWERS = [{"question_id": "q1", "answer_text": "PDFs and markdown files"}]


@pytest.mark.asyncio
async def test_session_respond_returns_revised_prompt_and_analysis(api_client):
    mock_reformulation = MagicMock()
    mock_reformulation.reformulated_query = MagicMock(
        category="rag_patterns",
        concept_tags=["chunking"],
        query_text="Document chunking strategies for RAG",
        model_dump=lambda: {
            "category": "rag_patterns",
            "concept_tags": ["chunking"],
            "query_text": "Document chunking strategies for RAG",
        },
    )

    mock_synthesis = MagicMock()
    mock_synthesis.revised_prompt = "Revised: How do I chunk PDFs for RAG?"
    mock_synthesis.analysis = "Added specificity around document types."

    with (
        patch(
            "backend.services.session_service.reformulation_agent.run",
            new=AsyncMock(return_value=mock_reformulation),
        ),
        patch(
            "backend.services.session_service.embed_text",
            new=AsyncMock(return_value=[0.1] * 1536),
        ),
        patch(
            "backend.services.session_service.retrieve",
            new=AsyncMock(return_value=[]),
        ),
        patch(
            "backend.services.session_service.synthesizer_agent.run",
            new=AsyncMock(return_value=mock_synthesis),
        ),
        patch("backend.agents.base.get_anthropic_client", return_value=AsyncMock()),
        patch("backend.dependencies.get_db", return_value=AsyncMock()),
    ):
        response = await api_client.post(
            "/api/v1/session/respond",
            json={"session_context": _SESSION_CONTEXT, "answers": _ANSWERS},
        )

    assert response.status_code == 200
    data = response.json()
    assert "revised_prompt" in data
    assert "analysis" in data
    assert data["original_prompt"] == "How do I chunk documents for RAG?"
