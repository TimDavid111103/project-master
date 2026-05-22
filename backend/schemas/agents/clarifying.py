from pydantic import BaseModel

from backend.schemas.agents.common import ClarifyingQuestion


# Used during prompt sessions: clarify what the user thinks their prompt does
class ClarifyingAgentInput(BaseModel):
    original_prompt: str
    project_definition: str | None
    previous_questions: list[str]


class ClarifyingAgentOutput(BaseModel):
    questions: list[ClarifyingQuestion]


# Used during project setup: refine a rough idea into a concrete project definition
class ProjectSetupAgentInput(BaseModel):
    project_name: str
    rough_idea: str


class ProjectSetupAgentOutput(BaseModel):
    questions: list[ClarifyingQuestion]


class ProjectDefinitionAgentInput(BaseModel):
    project_name: str
    rough_idea: str
    qa_pairs: list  # list of QAPair from retrieval schema


class ProjectDefinitionAgentOutput(BaseModel):
    project_definition: str
