"""Pipeline orchestration for both the project setup flow and prompt session flow.

Single responsibility: wire agents, memory service, and retrieval in the correct order.
No HTTP concerns, no direct DB queries beyond what is delegated to memory_service.
"""
import uuid

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import analysis_agent, clarifying_agent
from backend.config import Settings
from backend.schemas.agents.analysis import IntentTranslationAgentInput
from backend.schemas.agents.clarifying import (
    ClarifyingAgentInput,
    ClarifyingAgentOutput,
    ProjectDefinitionAgentInput,
    ProjectSetupAgentInput,
    ProjectSetupAgentOutput,
)
from backend.schemas.agents.common import UserAnswer
from backend.schemas.agents.retrieval import QAPair
from backend.schemas.api.projects import ProjectSetupContext, ProjectSetupRespondResponse
from backend.schemas.api.session import SessionContext, SessionRespondResponse
from backend.services import memory_service


# ---------------------------------------------------------------------------
# Flow 1 — Project setup
# ---------------------------------------------------------------------------


async def run_setup_start_pipeline(
    project_id: uuid.UUID,
    project_name: str,
    rough_idea: str,
    client: anthropic.AsyncAnthropic,
) -> ProjectSetupAgentOutput:
    return await clarifying_agent.run_project_setup_questions(
        client,
        ProjectSetupAgentInput(project_name=project_name, rough_idea=rough_idea),
    )


async def run_setup_respond_pipeline(
    setup_context: ProjectSetupContext,
    answers: list[UserAnswer],
    client: anthropic.AsyncAnthropic,
    db: AsyncSession,
) -> ProjectSetupRespondResponse:
    qa_pairs = [
        QAPair(question_text=q.question_text, answer_text=a.answer_text)
        for q, a in zip(setup_context.questions, answers)
    ]

    # Retrieve project name for the definition synthesis
    from backend.db.models import Project
    from sqlalchemy import select
    result = await db.execute(select(Project).where(Project.id == setup_context.project_id))
    project = result.scalar_one()

    definition_output = await clarifying_agent.run_project_definition(
        client,
        ProjectDefinitionAgentInput(
            project_name=project.name,
            rough_idea=setup_context.rough_idea,
            qa_pairs=qa_pairs,
        ),
    )

    await memory_service.store_project_definition(
        db, setup_context.project_id, definition_output.project_definition
    )

    return ProjectSetupRespondResponse(
        project_id=setup_context.project_id,
        project_definition=definition_output.project_definition,
    )


# ---------------------------------------------------------------------------
# Flow 2 — Prompt session
# ---------------------------------------------------------------------------


async def run_start_pipeline(
    original_prompt: str,
    project_id: uuid.UUID,
    client: anthropic.AsyncAnthropic,
    db: AsyncSession,
    settings: Settings,
) -> ClarifyingAgentOutput:
    memory = await memory_service.load_memory(db, project_id, original_prompt, settings)
    await memory_service.store_raw_prompt(db, project_id, original_prompt, settings)
    return await clarifying_agent.run(
        client,
        ClarifyingAgentInput(
            original_prompt=original_prompt,
            project_definition=memory.project_definition,
            previous_questions=memory.previous_questions,
        ),
    )


async def run_respond_pipeline(
    context: SessionContext,
    answers: list[UserAnswer],
    client: anthropic.AsyncAnthropic,
    db: AsyncSession,
    settings: Settings,
    taxonomy: dict,
) -> SessionRespondResponse:
    project_id = context.project_id
    memory = await memory_service.load_memory(
        db, project_id, context.original_prompt, settings
    )

    qa_pairs = [
        QAPair(question_text=q.question_text, answer_text=a.answer_text)
        for q, a in zip(context.questions, answers)
    ]

    await memory_service.store_qa_pairs(db, project_id, qa_pairs, settings)

    translation_output = await analysis_agent.run(
        client,
        IntentTranslationAgentInput(
            original_prompt=context.original_prompt,
            qa_pairs=qa_pairs,
            project_definition=memory.project_definition,
            past_translations=memory.past_translations,
        ),
    )

    await memory_service.store_translation(
        db,
        project_id,
        context.original_prompt,
        translation_output.intent_translation,
        settings,
    )

    return SessionRespondResponse(
        original_prompt=context.original_prompt,
        intent_translation=translation_output.intent_translation,
    )
