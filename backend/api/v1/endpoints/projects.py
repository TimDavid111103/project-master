"""Project management endpoints."""
import json
import uuid as _uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from backend.db.models import Project
from backend.dependencies import DbDep
from backend.schemas.agents.ideation import ProjectPlan
from backend.schemas.agents.tech_stack import TechStack
from backend.schemas.api.projects import (
    CreateProjectRequest,
    CreateProjectResponse,
    ProjectDetailResponse,
    ProjectListItem,
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


@router.get("", response_model=list[ProjectListItem])
async def list_projects(db: DbDep) -> list[ProjectListItem]:
    result = await db.execute(select(Project).order_by(Project.created_at.desc()))
    projects = result.scalars().all()
    return [
        ProjectListItem(
            project_id=p.id,
            name=p.name,
            rough_idea=p.rough_idea,
            is_complete=p.project_plan_json is not None and p.tech_stack_json is not None,
            created_at=p.created_at,
        )
        for p in projects
    ]


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(project_id: str, db: DbDep) -> ProjectDetailResponse:
    pid = _uuid.UUID(project_id)
    result = await db.execute(select(Project).where(Project.id == pid))
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    project_plan = (
        ProjectPlan.model_validate_json(project.project_plan_json)
        if project.project_plan_json
        else None
    )
    tech_stack = (
        TechStack.model_validate_json(project.tech_stack_json)
        if project.tech_stack_json
        else None
    )

    return ProjectDetailResponse(
        project_id=project.id,
        name=project.name,
        rough_idea=project.rough_idea,
        is_complete=project_plan is not None and tech_stack is not None,
        project_plan=project_plan,
        tech_stack=tech_stack,
        created_at=project.created_at,
    )
