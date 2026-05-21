"""Pipeline orchestration for the session flow.

Single responsibility: wire agents, memory service, and retrieval in the correct order.
No HTTP concerns, no direct DB queries beyond what is delegated to memory_service.
"""
import uuid

import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import analysis_agent, clarifying_agent, retrieval_agent
from backend.config import Settings
from backend.schemas.agents.analysis import AnalysisAgentInput
from backend.schemas.agents.clarifying import ClarifyingAgentInput, ClarifyingAgentOutput
from backend.schemas.agents.common import UserAnswer
from backend.schemas.agents.retrieval import QAPair, RetrievalAgentInput
from backend.schemas.api.session import SessionContext, SessionRespondResponse
from backend.services import memory_service


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
            project_summary=memory.project_summary,
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

    retrieval_output = await retrieval_agent.run(
        client,
        RetrievalAgentInput(
            original_prompt=context.original_prompt,
            qa_pairs=qa_pairs,
            project_summary=memory.project_summary,
            taxonomy=taxonomy,
        ),
        db,
        settings,
    )

    await memory_service.store_qa_pairs(db, project_id, qa_pairs, settings)

    analysis_output = await analysis_agent.run(
        client,
        AnalysisAgentInput(
            original_prompt=context.original_prompt,
            qa_pairs=qa_pairs,
            retrieved_documents=retrieval_output.retrieved_docs,
            project_summary=memory.project_summary,
            past_analyses=memory.past_analyses,
        ),
    )

    await memory_service.store_analysis(
        db, project_id, context.original_prompt, analysis_output.analysis, settings
    )

    return SessionRespondResponse(
        original_prompt=context.original_prompt,
        analysis=analysis_output.analysis,
        retrieved_documents=retrieval_output.retrieved_docs,
    )
