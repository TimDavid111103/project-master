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


class TechStackAgentOutput(BaseModel):
    tech_stack: TechStack
