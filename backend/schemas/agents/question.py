from pydantic import BaseModel

from .common import ClarifyingQuestion


class QuestionAgentInput(BaseModel):
    original_prompt: str


class QuestionAgentOutput(BaseModel):
    questions: list[ClarifyingQuestion]
