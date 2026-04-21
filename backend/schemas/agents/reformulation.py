from pydantic import BaseModel

from .common import ClarifyingQuestion, UserAnswer


class ReformulatedQuery(BaseModel):
    category: str
    concept_tags: list[str]
    query_text: str


class ReformulationAgentInput(BaseModel):
    original_prompt: str
    questions: list[ClarifyingQuestion]
    answers: list[UserAnswer]
    taxonomy: dict


class ReformulationAgentOutput(BaseModel):
    reformulated_query: ReformulatedQuery
