"""Orchestrates the project planning pipeline: RAG retrieval → tech stack generation → DB persistence."""
import uuid

import anthropic
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import retrieval_agent, tech_stack_agent
from backend.config import Settings
from backend.db.models import Project
from backend.schemas.agents.ideation import ProjectPlan
from backend.schemas.agents.retrieval import RetrievalAgentInput
from backend.schemas.agents.tech_stack import TechStack, TechStackAgentInput
from backend.schemas.api.pipeline import PipelineAnalyzeResponse


async def run_analyze_pipeline(
    project_id: str,
    project_plan: ProjectPlan,
    client: anthropic.AsyncAnthropic,
    db: AsyncSession,
    settings: Settings,
) -> PipelineAnalyzeResponse:
    retrieval_output = await retrieval_agent.run(
        client,
        RetrievalAgentInput(project_plan=project_plan),
        db,
        settings,
    )

    retrieved_contents = [doc.content for doc in retrieval_output.retrieved_docs]

    tech_stack_output = await tech_stack_agent.run(
        client,
        TechStackAgentInput(
            project_plan=project_plan,
            retrieved_doc_contents=retrieved_contents,
        ),
    )

    pid = uuid.UUID(project_id)
    result = await db.execute(select(Project).where(Project.id == pid))
    project = result.scalar_one()
    project.project_plan_json = project_plan.model_dump_json()
    project.tech_stack_json = tech_stack_output.tech_stack.model_dump_json()
    await db.commit()

    return PipelineAnalyzeResponse(
        project_plan=project_plan,
        tech_stack=tech_stack_output.tech_stack,
    )
