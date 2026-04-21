from pydantic import BaseModel

from backend.schemas.agents.common import ClarifyingQuestion, UserAnswer
from backend.schemas.agents.reformulation import ReformulatedQuery
from backend.schemas.agents.synthesizer import RetrievedDocument


class SessionContext(BaseModel):
    """Stateless blob returned by /start and echoed in /respond body."""
    original_prompt: str
    questions: list[ClarifyingQuestion]


class SessionStartRequest(BaseModel):
    original_prompt: str


class SessionStartResponse(BaseModel):
    session_context: SessionContext
    questions: list[ClarifyingQuestion]


class SessionRespondRequest(BaseModel):
    session_context: SessionContext
    answers: list[UserAnswer]


class SessionRespondResponse(BaseModel):
    original_prompt: str
    revised_prompt: str
    analysis: str
    reformulated_query: ReformulatedQuery
    retrieved_documents: list[RetrievedDocument]
