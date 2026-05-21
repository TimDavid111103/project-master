import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.schemas.agents.analysis import DimensionGrade, PromptAnalysis
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
async def test_session_respond_returns_prompt_analysis(api_client):
    mock_response = SessionRespondResponse(
        original_prompt="How do I chunk documents for RAG?",
        analysis=PromptAnalysis(
            intent_accuracy=DimensionGrade(
                grade="B",
                explanation="Prompt mostly reflects the intent revealed in Q&A.",
            ),
            technical_language=DimensionGrade(
                grade="A",
                explanation="Technical depth is appropriate for the task complexity.",
            ),
            standards_alignment=DimensionGrade(
                grade="B",
                explanation="Follows most conventions for RAG engineering prompts.",
            ),
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

    assert "analysis" in data
    assert "intent_accuracy" in data["analysis"]
    assert "technical_language" in data["analysis"]
    assert "standards_alignment" in data["analysis"]
    assert data["analysis"]["intent_accuracy"]["grade"] == "B"
    assert data["analysis"]["intent_accuracy"]["explanation"] != ""
    assert "revised_prompt" not in data
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
