"""HTTP concerns only: parse request, call service, return response."""
import json
import pathlib

from fastapi import APIRouter

from backend.agents.base import get_anthropic_client
from backend.dependencies import DbDep, SettingsDep
from backend.schemas.api.session import (
    SessionContext,
    SessionRespondRequest,
    SessionRespondResponse,
    SessionStartRequest,
    SessionStartResponse,
)
from backend.services.session_service import run_respond_pipeline, run_start_pipeline

router = APIRouter(prefix="/session", tags=["session"])

_TAXONOMY: dict = json.loads(pathlib.Path("taxonomy.json").read_text())


@router.post("/start", response_model=SessionStartResponse)
async def session_start(
    body: SessionStartRequest,
    db: DbDep,
    settings: SettingsDep,
) -> SessionStartResponse:
    client = get_anthropic_client()
    output = await run_start_pipeline(
        body.original_prompt,
        body.project_id,
        client,
        db,
        settings,
    )
    ctx = SessionContext(
        original_prompt=body.original_prompt,
        questions=output.questions,
        project_id=body.project_id,
    )
    return SessionStartResponse(session_context=ctx, questions=output.questions)


@router.post("/respond", response_model=SessionRespondResponse)
async def session_respond(
    body: SessionRespondRequest,
    db: DbDep,
    settings: SettingsDep,
) -> SessionRespondResponse:
    client = get_anthropic_client()
    return await run_respond_pipeline(
        body.session_context,
        body.answers,
        client,
        db,
        settings,
        _TAXONOMY,
    )
