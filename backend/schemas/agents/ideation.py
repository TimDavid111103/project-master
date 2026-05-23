from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ProjectPlan(BaseModel):
    vision: str
    target_audience: str
    problem_addressed: str
    mvp_scope: str


class IdeationChatOutput(BaseModel):
    agent_message: str
    is_complete: bool
    project_plan: ProjectPlan | None
