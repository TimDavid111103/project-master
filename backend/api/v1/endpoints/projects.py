"""Project management endpoints."""
from fastapi import APIRouter

from backend.db.models import Project
from backend.dependencies import DbDep
from backend.schemas.api.projects import CreateProjectRequest, CreateProjectResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=CreateProjectResponse, status_code=201)
async def create_project(
    body: CreateProjectRequest,
    db: DbDep,
) -> CreateProjectResponse:
    project = Project(name=body.name, summary=body.summary)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return CreateProjectResponse(
        project_id=project.id,
        name=project.name,
        summary=project.summary,
        created_at=project.created_at,
    )
