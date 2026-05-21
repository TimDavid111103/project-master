"""Offline script: chunk, tag, embed, and store corpus documents in pgvector.

Usage:
    uv run python scripts/ingest.py --corpus-dir corpus/ --taxonomy taxonomy.json

Run taxonomy_discovery.py and finalize taxonomy.json before running this script.
"""
import argparse
import asyncio
import json
import pathlib
import sys
import uuid

_ROOT = pathlib.Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import anthropic
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import get_settings
from backend.db.engine import async_session_factory
from backend.db.models import Document
from backend.rag.chunker import HierarchicalChunk, chunk_document
from backend.rag.embedder import embed_text


class ChunkTagOutput(BaseModel):
    category: str
    concept_tags: list[str]


_TAG_SYSTEM_TEMPLATE = """\
You are a document classifier. Given a text chunk, assign it a category and concept tags
from the following taxonomy only. Do not invent new categories or tags.

Taxonomy:
{taxonomy}\
"""


async def tag_chunk(
    client: anthropic.AsyncAnthropic,
    chunk: str,
    taxonomy: dict,
    settings,
) -> ChunkTagOutput:
    system = _TAG_SYSTEM_TEMPLATE.format(taxonomy=json.dumps(taxonomy, indent=2))
    response = await client.messages.create(
        model=settings.claude_model,
        max_tokens=256,
        system=system,
        messages=[{"role": "user", "content": chunk}],
        tools=[
            {
                "name": "output_tags",
                "description": "Output the category and concept tags for this chunk.",
                "input_schema": ChunkTagOutput.model_json_schema(),
            }
        ],
        tool_choice={"type": "tool", "name": "output_tags"},
    )
    tool_block = next(b for b in response.content if b.type == "tool_use")
    return ChunkTagOutput.model_validate(tool_block.input)


async def ingest_file(
    path: pathlib.Path,
    client: anthropic.AsyncAnthropic,
    session: AsyncSession,
    taxonomy: dict,
    settings,
    batch_size: int = 10,
) -> int:
    chunks: list[HierarchicalChunk] = await chunk_document(path, client, settings)

    # --- First pass: insert section chunks and record their UUIDs ---
    # Section chunks are tagged and embedded so the Retrieval Agent can fetch them as context.
    section_uuids: dict[int, uuid.UUID] = {}  # position → uuid
    section_batch: list[Document] = []

    for position, chunk in enumerate(chunks):
        if chunk.chunk_level != "section":
            continue
        tags = await tag_chunk(client, chunk.content, taxonomy, settings)
        embedding = await embed_text(chunk.content, settings)
        doc_id = uuid.uuid4()
        section_uuids[position] = doc_id
        section_batch.append(
            Document(
                id=doc_id,
                source_file=str(path),
                chunk_index=position,
                content=chunk.content,
                category=tags.category,
                concept_tags=tags.concept_tags,
                embedding=embedding,
                parent_id=None,
                chunk_level="section",
                context_summary=None,
            )
        )

    session.add_all(section_batch)
    await session.commit()
    print(f"  Committed {len(section_batch)} section chunks from {path.name}")

    # --- Second pass: insert child chunks with parent_id and inherited tags ---
    # Tags are inherited from the parent section. Embedding uses context_summary + content.
    child_batch: list[Document] = []
    inserted = len(section_batch)

    for position, chunk in enumerate(chunks):
        if chunk.chunk_level != "chunk":
            continue

        parent_uuid: uuid.UUID | None = None
        if chunk.parent_position is not None:
            parent_uuid = section_uuids.get(chunk.parent_position)

        # Inherit tags from the parent section chunk if available
        parent_doc = next(
            (d for d in section_batch if d.id == parent_uuid), None
        )
        if parent_doc:
            category = parent_doc.category
            concept_tags = parent_doc.concept_tags
        else:
            # Orphaned child — tag independently
            tags = await tag_chunk(client, chunk.content, taxonomy, settings)
            category = tags.category
            concept_tags = tags.concept_tags

        # Embed context_summary prepended to content for richer representation
        embed_text_value = (
            f"{chunk.context_summary}\n\n{chunk.content}"
            if chunk.context_summary
            else chunk.content
        )
        embedding = await embed_text(embed_text_value, settings)

        child_batch.append(
            Document(
                id=uuid.uuid4(),
                source_file=str(path),
                chunk_index=position,
                content=chunk.content,
                category=category,
                concept_tags=concept_tags,
                embedding=embedding,
                parent_id=parent_uuid,
                chunk_level="chunk",
                context_summary=chunk.context_summary or None,
            )
        )

        if len(child_batch) >= batch_size:
            session.add_all(child_batch)
            await session.commit()
            inserted += len(child_batch)
            print(f"  Committed {inserted} total chunks from {path.name}...")
            child_batch = []

    if child_batch:
        session.add_all(child_batch)
        await session.commit()
        inserted += len(child_batch)

    return inserted


async def run_ingestion(corpus_dir: pathlib.Path, taxonomy_path: pathlib.Path) -> None:
    settings = get_settings()
    taxonomy = json.loads(taxonomy_path.read_text())
    if "_note" in taxonomy:
        del taxonomy["_note"]

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    files = list(corpus_dir.glob("**/*.txt")) + list(corpus_dir.glob("**/*.md")) + list(corpus_dir.glob("**/*.pdf"))
    if not files:
        print(f"No .txt, .md, or .pdf files found in {corpus_dir}.")
        return

    total = 0
    async for session in async_session_factory():
        for path in files:
            print(f"Ingesting {path.name}...")
            count = await ingest_file(path, client, session, taxonomy, settings)
            total += count
            print(f"  Done — {count} chunks stored.")

    print(f"\nIngestion complete. Total chunks stored: {total}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", default="corpus", type=pathlib.Path)
    parser.add_argument("--taxonomy", default="taxonomy.json", type=pathlib.Path)
    args = parser.parse_args()
    asyncio.run(run_ingestion(args.corpus_dir, args.taxonomy))
