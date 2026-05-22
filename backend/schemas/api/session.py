import uuid

from pydantic import BaseModel

from backend.schemas.agents.analysis import IntentTranslation
from backend.schemas.agents.common import ClarifyingQuestion, UserAnswer
from backend.schemas.agents.retrieval import RetrievedDocResult


class SessionContext(BaseModel):
    """Stateless blob returned by /start and echoed in /respond body."""
    original_prompt: str
    questions: list[ClarifyingQuestion]
    project_id: uuid.UUID


class SessionStartRequest(BaseModel):
    original_prompt: str
    project_id: uuid.UUID


class SessionStartResponse(BaseModel):
    session_context: SessionContext
    questions: list[ClarifyingQuestion]


class SessionRespondRequest(BaseModel):
    session_context: SessionContext
    answers: list[UserAnswer]


class SessionRespondResponse(BaseModel):
    original_prompt: str
    intent_translation: IntentTranslation
    retrieved_documents: list[RetrievedDocResult]
