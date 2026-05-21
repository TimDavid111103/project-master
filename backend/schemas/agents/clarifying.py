from pydantic import BaseModel

from backend.schemas.agents.common import ClarifyingQuestion


class ClarifyingAgentInput(BaseModel):
    original_prompt: str
    project_summary: str | None
    previous_questions: list[str]


class ClarifyingAgentOutput(BaseModel):
    questions: list[ClarifyingQuestion]
