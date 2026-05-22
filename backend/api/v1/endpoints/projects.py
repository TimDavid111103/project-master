"""Project management and project setup endpoints."""
from fastapi import APIRouter

from backend.agents.base import get_anthropic_client
from backend.db.models import Project
from backend.dependencies import DbDep
from backend.schemas.api.projects import (
    CreateProjectRequest,
    CreateProjectResponse,
    ProjectSetupRespondRequest,
    ProjectSetupRespondResponse,
    ProjectSetupStartResponse,
    ProjectSetupContext,
)
from backend.services.session_service import (
    run_setup_respond_pipeline,
    run_setup_start_pipeline,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=CreateProjectResponse, status_code=201)
async def create_project(
    body: CreateProjectRequest,
    db: DbDep,
) -> CreateProjectResponse:
    project = Project(name=body.name, rough_idea=body.rough_idea)
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return CreateProjectResponse(
        project_id=project.id,
        name=project.name,
        rough_idea=project.rough_idea,
        created_at=project.created_at,
    )


@router.post("/{project_id}/setup/start", response_model=ProjectSetupStartResponse)
async def project_setup_start(
    project_id: str,
    db: DbDep,
) -> ProjectSetupStartResponse:
    from sqlalchemy import select
    import uuid as _uuid

    pid = _uuid.UUID(project_id)
    result = await db.execute(select(Project).where(Project.id == pid))
    project = result.scalar_one()

    client = get_anthropic_client()
    output = await run_setup_start_pipeline(
        project_id=pid,
        project_name=project.name,
        rough_idea=project.rough_idea,
        client=client,
    )

    ctx = ProjectSetupContext(
        project_id=pid,
        rough_idea=project.rough_idea,
        questions=output.questions,
    )
    return ProjectSetupStartResponse(setup_context=ctx, questions=output.questions)


@router.post("/{project_id}/setup/respond", response_model=ProjectSetupRespondResponse)
async def project_setup_respond(
    project_id: str,
    body: ProjectSetupRespondRequest,
    db: DbDep,
) -> ProjectSetupRespondResponse:
    client = get_anthropic_client()
    return await run_setup_respond_pipeline(
        setup_context=body.setup_context,
        answers=body.answers,
        client=client,
        db=db,
    )
