from pydantic import BaseModel

from backend.schemas.agents.ideation import ChatMessage, ProjectPlan
from backend.schemas.agents.tech_stack import TechStack


class PipelineChatRequest(BaseModel):
    user_message: str
    conversation_history: list[ChatMessage]


class PipelineChatResponse(BaseModel):
    agent_message: str
    is_complete: bool
    project_plan: ProjectPlan | None


class PipelineAnalyzeRequest(BaseModel):
    project_id: str
    project_plan: ProjectPlan
    user_tech_stack: list[str] = []


class PipelineAnalyzeResponse(BaseModel):
    project_plan: ProjectPlan
    tech_stack: TechStack
