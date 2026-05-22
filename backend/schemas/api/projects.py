import uuid
from datetime import datetime

from pydantic import BaseModel

from backend.schemas.agents.common import ClarifyingQuestion, UserAnswer
from backend.schemas.agents.analysis import IntentTranslation


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
    definition: str | None
    created_at: datetime


class PromptSessionRecord(BaseModel):
    session_id: uuid.UUID
    original_prompt: str
    intent_translation: IntentTranslation
    created_at: datetime


class ProjectHistoryResponse(BaseModel):
    project_id: uuid.UUID
    name: str
    rough_idea: str
    definition: str | None
    created_at: datetime
    sessions: list[PromptSessionRecord]


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
