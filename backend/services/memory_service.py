"""Project memory: read and write per-project session history.

Memory stores raw prompts, Q&A pairs, and intent translations for each project.

Context window strategy:
  - Below settings.memory_session_threshold entries: pass all memory directly.
  - At or above threshold: embed the current prompt and retrieve the most similar
    entries via cosine similarity from each memory table.

Note: previous_questions is ALWAYS fetched in full regardless of threshold,
because it is a hard constraint for question deduplication — not context enrichment.
"""
import json
import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings
from backend.db.models import Project, PromptAnalysisRecord, QAPairRecord, RawPrompt
from backend.rag.embedder import embed_text
from backend.schemas.agents.analysis import IntentTranslation
from backend.schemas.agents.retrieval import QAPair
from backend.schemas.memory import ProjectMemory


async def _get_project(db: AsyncSession, project_id: uuid.UUID) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    project = result.scalar_one_or_none()
    if project is None:
        raise ValueError(f"Project {project_id} not found")
    return project


async def _count_entries(db: AsyncSession, project_id: uuid.UUID) -> int:
    raw_count = (
        await db.execute(
            select(func.count()).select_from(RawPrompt).where(RawPrompt.project_id == project_id)
        )
    ).scalar_one()
    qa_count = (
        await db.execute(
            select(func.count())
            .select_from(QAPairRecord)
            .where(QAPairRecord.project_id == project_id)
        )
    ).scalar_one()
    analysis_count = (
        await db.execute(
            select(func.count())
            .select_from(PromptAnalysisRecord)
            .where(PromptAnalysisRecord.project_id == project_id)
        )
    ).scalar_one()
    return raw_count + qa_count + analysis_count


async def _all_previous_questions(db: AsyncSession, project_id: uuid.UUID) -> list[str]:
    rows = (
        await db.execute(
            select(QAPairRecord.question_text)
            .where(QAPairRecord.project_id == project_id)
            .order_by(QAPairRecord.session_at)
        )
    ).scalars().all()
    return list(rows)


def _serialize_translation(record: PromptAnalysisRecord) -> str:
    assumptions = json.loads(record.assumptions_made)
    gaps = json.loads(record.potential_gaps)
    return (
        f"Prompt: {record.original_prompt[:200]}\n"
        f"What it instructs: {record.what_the_prompt_instructs}\n"
        f"Assumptions: {'; '.join(assumptions)}\n"
        f"Gaps: {'; '.join(gaps)}"
    )


async def _load_all_memory(
    db: AsyncSession, project_id: uuid.UUID, definition: str | None
) -> ProjectMemory:
    raw_rows = (
        await db.execute(
            select(RawPrompt.content)
            .where(RawPrompt.project_id == project_id)
            .order_by(RawPrompt.created_at)
        )
    ).scalars().all()

    qa_rows = (
        await db.execute(
            select(QAPairRecord)
            .where(QAPairRecord.project_id == project_id)
            .order_by(QAPairRecord.session_at)
        )
    ).scalars().all()

    analysis_rows = (
        await db.execute(
            select(PromptAnalysisRecord)
            .where(PromptAnalysisRecord.project_id == project_id)
            .order_by(PromptAnalysisRecord.created_at)
        )
    ).scalars().all()

    return ProjectMemory(
        project_id=project_id,
        project_definition=definition,
        past_raw_prompts=list(raw_rows),
        past_qa_pairs=[
            QAPair(question_text=r.question_text, answer_text=r.answer_text)
            for r in qa_rows
        ],
        past_translations=[_serialize_translation(r) for r in analysis_rows],
        previous_questions=[r.question_text for r in qa_rows],
    )


async def _load_similar_memory(
    db: AsyncSession,
    project_id: uuid.UUID,
    definition: str | None,
    query_embedding: list[float],
    top_k: int,
) -> ProjectMemory:
    raw_rows = (
        await db.execute(
            select(RawPrompt.content)
            .where(RawPrompt.project_id == project_id)
            .where(RawPrompt.embedding.is_not(None))
            .order_by(RawPrompt.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
    ).scalars().all()

    qa_rows = (
        await db.execute(
            select(QAPairRecord)
            .where(QAPairRecord.project_id == project_id)
            .where(QAPairRecord.embedding.is_not(None))
            .order_by(QAPairRecord.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
    ).scalars().all()

    analysis_rows = (
        await db.execute(
            select(PromptAnalysisRecord)
            .where(PromptAnalysisRecord.project_id == project_id)
            .where(PromptAnalysisRecord.embedding.is_not(None))
            .order_by(PromptAnalysisRecord.embedding.cosine_distance(query_embedding))
            .limit(top_k)
        )
    ).scalars().all()

    all_questions = await _all_previous_questions(db, project_id)

    return ProjectMemory(
        project_id=project_id,
        project_definition=definition,
        past_raw_prompts=list(raw_rows),
        past_qa_pairs=[
            QAPair(question_text=r.question_text, answer_text=r.answer_text)
            for r in qa_rows
        ],
        past_translations=[_serialize_translation(r) for r in analysis_rows],
        previous_questions=all_questions,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def load_memory(
    db: AsyncSession,
    project_id: uuid.UUID,
    current_prompt: str,
    settings: Settings,
) -> ProjectMemory:
    project = await _get_project(db, project_id)
    total = await _count_entries(db, project_id)

    if total < settings.memory_session_threshold:
        return await _load_all_memory(db, project_id, project.definition)

    query_embedding = await embed_text(current_prompt, settings)
    return await _load_similar_memory(
        db, project_id, project.definition, query_embedding, settings.memory_top_k
    )


async def store_project_definition(
    db: AsyncSession,
    project_id: uuid.UUID,
    definition: str,
) -> None:
    project = await _get_project(db, project_id)
    project.definition = definition
    await db.commit()


async def store_raw_prompt(
    db: AsyncSession,
    project_id: uuid.UUID,
    content: str,
    settings: Settings,
) -> None:
    embedding = await embed_text(content, settings)
    db.add(RawPrompt(project_id=project_id, content=content, embedding=embedding))
    await db.commit()


async def store_qa_pairs(
    db: AsyncSession,
    project_id: uuid.UUID,
    qa_pairs: list[QAPair],
    settings: Settings,
) -> None:
    for pair in qa_pairs:
        combined = f"{pair.question_text} {pair.answer_text}"
        embedding = await embed_text(combined, settings)
        db.add(
            QAPairRecord(
                project_id=project_id,
                question_text=pair.question_text,
                answer_text=pair.answer_text,
                embedding=embedding,
            )
        )
    await db.commit()


async def store_translation(
    db: AsyncSession,
    project_id: uuid.UUID,
    original_prompt: str,
    translation: IntentTranslation,
    settings: Settings,
) -> None:
    summary_text = f"{original_prompt} {translation.model_dump_json()}"
    embedding = await embed_text(summary_text, settings)
    db.add(
        PromptAnalysisRecord(
            project_id=project_id,
            original_prompt=original_prompt,
            what_the_prompt_instructs=translation.what_the_prompt_instructs,
            assumptions_made=json.dumps(translation.assumptions_made),
            potential_gaps=json.dumps(translation.potential_gaps),
            embedding=embedding,
        )
    )
    await db.commit()
