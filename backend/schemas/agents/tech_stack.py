from pydantic import BaseModel

from backend.schemas.agents.ideation import ProjectPlan


class TechStackItem(BaseModel):
    name: str
    category: str
    rationale: str


class TechStack(BaseModel):
    mvp: list[TechStackItem]
    full_product: list[TechStackItem]


class TechStackAgentInput(BaseModel):
    project_plan: ProjectPlan
    user_tech_stack: list[str] = []


class TechStackAgentOutput(BaseModel):
    tech_stack: TechStack
