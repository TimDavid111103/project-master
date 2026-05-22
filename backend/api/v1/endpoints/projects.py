"""Project management and project setup endpoints."""
import json
import uuid as _uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from backend.agents.base import get_anthropic_client
from backend.db.models import Project, PromptAnalysisRecord
from backend.dependencies import DbDep
from backend.schemas.agents.analysis import IntentTranslation
from backend.schemas.api.projects import (
    CreateProjectRequest,
    CreateProjectResponse,
    ProjectHistoryResponse,
    ProjectListItem,
    ProjectSetupRespondRequest,
    ProjectSetupRespondResponse,
    ProjectSetupStartResponse,
    ProjectSetupContext,
    PromptSessionRecord,
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


@router.get("", response_model=list[ProjectListItem])
async def list_projects(db: DbDep) -> list[ProjectListItem]:
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    return [
        ProjectListItem(
            project_id=p.id,
            name=p.name,
            rough_idea=p.rough_idea,
            definition=p.definition,
            created_at=p.created_at,
        )
        for p in projects
    ]


@router.get("/{project_id}/history", response_model=ProjectHistoryResponse)
async def project_history(project_id: str, db: DbDep) -> ProjectHistoryResponse:
    pid = _uuid.UUID(project_id)
    result = await db.execute(select(Project).where(Project.id == pid))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    analyses_result = await db.execute(
        select(PromptAnalysisRecord)
        .where(PromptAnalysisRecord.project_id == pid)
        .order_by(PromptAnalysisRecord.created_at.desc())
    )
    analyses = analyses_result.scalars().all()

    sessions = [
        PromptSessionRecord(
            session_id=a.id,
            original_prompt=a.original_prompt,
            intent_translation=IntentTranslation(
                what_the_prompt_instructs=a.what_the_prompt_instructs,
                assumptions_made=json.loads(a.assumptions_made),
                potential_gaps=json.loads(a.potential_gaps),
            ),
            created_at=a.created_at,
        )
        for a in analyses
    ]

    return ProjectHistoryResponse(
        project_id=project.id,
        name=project.name,
        rough_idea=project.rough_idea,
        definition=project.definition,
        created_at=project.created_at,
        sessions=sessions,
    )
