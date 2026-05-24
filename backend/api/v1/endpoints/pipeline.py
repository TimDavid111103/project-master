"""Pipeline endpoints: ideation chat turn and full analysis (tech stack generation)."""
from fastapi import APIRouter

from backend.agents import ideation_agent
from backend.agents.base import get_anthropic_client
from backend.dependencies import DbDep
from backend.schemas.api.pipeline import (
    PipelineAnalyzeRequest,
    PipelineAnalyzeResponse,
    PipelineChatRequest,
    PipelineChatResponse,
)
from backend.services.pipeline_service import run_analyze_pipeline

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.post("/chat", response_model=PipelineChatResponse)
async def pipeline_chat(body: PipelineChatRequest) -> PipelineChatResponse:
    client = get_anthropic_client()
    output = await ideation_agent.run(
        client,
        user_message=body.user_message,
        conversation_history=body.conversation_history,
    )
    return PipelineChatResponse(
        agent_message=output.agent_message,
        is_complete=output.is_complete,
        project_plan=output.project_plan,
    )


@router.post("/analyze", response_model=PipelineAnalyzeResponse)
async def pipeline_analyze(
    body: PipelineAnalyzeRequest,
    db: DbDep,
) -> PipelineAnalyzeResponse:
    client = get_anthropic_client()
    return await run_analyze_pipeline(
        project_id=body.project_id,
        project_plan=body.project_plan,
        user_tech_stack=body.user_tech_stack,
        client=client,
        db=db,
    )
