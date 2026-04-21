"""Pipeline orchestration for the session flow.

Single responsibility: wire agents, embedder, and retriever in the correct order.
No HTTP concerns, no direct DB queries.
"""
import anthropic
from sqlalchemy.ext.asyncio import AsyncSession

from backend.agents import question_agent, reformulation_agent, synthesizer_agent
from backend.config import Settings
from backend.rag.embedder import embed_text
from backend.rag.retriever import retrieve
from backend.schemas.agents.question import QuestionAgentInput, QuestionAgentOutput
from backend.schemas.agents.reformulation import ReformulationAgentInput
from backend.schemas.agents.synthesizer import SynthesizerAgentInput
from backend.schemas.agents.common import UserAnswer
from backend.schemas.api.session import SessionContext, SessionRespondResponse


async def run_start_pipeline(
    original_prompt: str,
    client: anthropic.AsyncAnthropic,
) -> QuestionAgentOutput:
    return await question_agent.run(
        client, QuestionAgentInput(original_prompt=original_prompt)
    )


async def run_respond_pipeline(
    context: SessionContext,
    answers: list[UserAnswer],
    client: anthropic.AsyncAnthropic,
    db: AsyncSession,
    settings: Settings,
    taxonomy: dict,
) -> SessionRespondResponse:
    reform_output = await reformulation_agent.run(
        client,
        ReformulationAgentInput(
            original_prompt=context.original_prompt,
            questions=context.questions,
            answers=answers,
            taxonomy=taxonomy,
        ),
    )
    rq = reform_output.reformulated_query

    query_embedding = await embed_text(rq.query_text, settings)
    docs = await retrieve(db, rq, query_embedding, top_k=settings.rag_top_k)

    synth_output = await synthesizer_agent.run(
        client,
        SynthesizerAgentInput(
            original_prompt=context.original_prompt,
            reformulated_query=rq,
            retrieved_documents=docs,
            answers=answers,
        ),
    )

    return SessionRespondResponse(
        original_prompt=context.original_prompt,
        revised_prompt=synth_output.revised_prompt,
        analysis=synth_output.analysis,
        reformulated_query=rq,
        retrieved_documents=docs,
    )
