import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.schemas.agents.analysis import IntentTranslation
from backend.schemas.agents.retrieval import RetrievedDocResult
from backend.schemas.api.session import SessionRespondResponse

_PROJECT_ID = str(uuid.uuid4())

_SESSION_CONTEXT = {
    "original_prompt": "How do I chunk documents for RAG?",
    "questions": [
        {
            "question_id": "q1",
            "question_text": "What document types will you process?",
            "rationale": "Affects chunking strategy selection",
        }
    ],
    "project_id": _PROJECT_ID,
}

_ANSWERS = [{"question_id": "q1", "answer_text": "PDFs and markdown files"}]


@pytest.mark.asyncio
async def test_session_respond_returns_intent_translation(api_client):
    mock_response = SessionRespondResponse(
        original_prompt="How do I chunk documents for RAG?",
        intent_translation=IntentTranslation(
            what_the_prompt_instructs="The prompt instructs the AI to explain document chunking strategies for retrieval-augmented generation.",
            assumptions_made=["The user is familiar with RAG pipelines", "The output should be explanatory rather than executable code"],
            potential_gaps=["No output format specified", "Document size constraints not mentioned"],
        ),
        retrieved_documents=[
            RetrievedDocResult(
                doc_id="abc123",
                content="Chunking strategies for RAG...",
                similarity_score=0.91,
                chunk_level="chunk",
                parent_id=None,
            )
        ],
    )

    with (
        patch(
            "backend.api.v1.endpoints.session.run_respond_pipeline",
            new=AsyncMock(return_value=mock_response),
        ),
        patch("backend.agents.base.get_anthropic_client", return_value=MagicMock()),
    ):
        response = await api_client.post(
            "/api/v1/session/respond",
            json={"session_context": _SESSION_CONTEXT, "answers": _ANSWERS},
        )

    assert response.status_code == 200
    data = response.json()

    assert "intent_translation" in data
    assert "what_the_prompt_instructs" in data["intent_translation"]
    assert "assumptions_made" in data["intent_translation"]
    assert "potential_gaps" in data["intent_translation"]
    assert isinstance(data["intent_translation"]["assumptions_made"], list)
    assert isinstance(data["intent_translation"]["potential_gaps"], list)
    assert "analysis" not in data
    assert data["original_prompt"] == "How do I chunk documents for RAG?"
    assert "retrieved_documents" in data
    assert data["retrieved_documents"][0]["doc_id"] == "abc123"


@pytest.mark.asyncio
async def test_session_respond_missing_project_id_returns_422(api_client):
    context_without_project = {
        "original_prompt": "How do I chunk?",
        "questions": [],
    }
    response = await api_client.post(
        "/api/v1/session/respond",
        json={"session_context": context_without_project, "answers": []},
    )
    assert response.status_code == 422
