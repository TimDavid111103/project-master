import uuid
from datetime import datetime

from pydantic import BaseModel

from backend.schemas.agents.ideation import ProjectPlan
from backend.schemas.agents.tech_stack import TechStack


class CreateProjectRequest(BaseModel):
    name: str
    rough_idea: str


class CreateProjectResponse(BaseModel):
    project_id: uuid.UUID
    name: str
    rough_idea: str
    created_at: datetime


class ProjectListItem(BaseModel):
    project_id: uuid.UUID
    name: str
    rough_idea: str
    is_complete: bool
    created_at: datetime


class ProjectDetailResponse(BaseModel):
    project_id: uuid.UUID
    name: str
    rough_idea: str
    is_complete: bool
    project_plan: ProjectPlan | None
    tech_stack: TechStack | None
    created_at: datetime
