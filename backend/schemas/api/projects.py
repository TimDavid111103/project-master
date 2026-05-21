import uuid
from datetime import datetime

from pydantic import BaseModel


class CreateProjectRequest(BaseModel):
    name: str
    summary: str


class CreateProjectResponse(BaseModel):
    project_id: uuid.UUID
    name: str
    summary: str
    created_at: datetime
