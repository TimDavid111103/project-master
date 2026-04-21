from pydantic import BaseModel

from .common import UserAnswer
from .reformulation import ReformulatedQuery


class RetrievedDocument(BaseModel):
    doc_id: str
    content: str
    similarity_score: float


class SynthesizerAgentInput(BaseModel):
    original_prompt: str
    reformulated_query: ReformulatedQuery
    retrieved_documents: list[RetrievedDocument]
    answers: list[UserAnswer]


class SynthesizerAgentOutput(BaseModel):
    revised_prompt: str
    analysis: str
