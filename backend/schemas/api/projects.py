import uuid
from datetime import datetime

from pydantic import BaseModel

from backend.schemas.agents.common import ClarifyingQuestion, UserAnswer


class CreateProjectRequest(BaseModel):
    name: str
    rough_idea: str


class CreateProjectResponse(BaseModel):
    project_id: uuid.UUID
    name: str
    rough_idea: str
    created_at: datetime


class ProjectSetupContext(BaseModel):
    """Stateless blob echoed from setup/start into setup/respond."""
    project_id: uuid.UUID
    rough_idea: str
    questions: list[ClarifyingQuestion]


class ProjectSetupStartResponse(BaseModel):
    setup_context: ProjectSetupContext
    questions: list[ClarifyingQuestion]


class ProjectSetupRespondRequest(BaseModel):
    setup_context: ProjectSetupContext
    answers: list[UserAnswer]


class ProjectSetupRespondResponse(BaseModel):
    project_id: uuid.UUID
    project_definition: str
