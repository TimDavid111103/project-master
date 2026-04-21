from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import Document
from backend.schemas.agents.reformulation import ReformulatedQuery
from backend.schemas.agents.synthesizer import RetrievedDocument


async def retrieve(
    session: AsyncSession,
    query: ReformulatedQuery,
    query_embedding: list[float],
    top_k: int = 5,
) -> list[RetrievedDocument]:
    """Two-stage retrieval: hard metadata filter then cosine similarity rank.

    Stage 1: filter by category (B-tree) and concept_tags containment (GIN @>).
    Stage 2: rank the filtered subset by cosine distance and take top_k.
    """
    stmt = (
        select(
            Document,
            Document.embedding.cosine_distance(query_embedding).label("distance"),
        )
        .where(Document.category == query.category)
        .where(Document.concept_tags.contains(query.concept_tags))
        .order_by("distance")
        .limit(top_k)
    )
    rows = (await session.execute(stmt)).all()
    return [
        RetrievedDocument(
            doc_id=str(row.Document.id),
            content=row.Document.content,
            similarity_score=round(1.0 - row.distance, 4),
        )
        for row in rows
    ]
