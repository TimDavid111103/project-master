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
from backend.rag.chunker import chunk_text
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
    text = path.read_text(encoding="utf-8", errors="ignore")
    chunks = chunk_text(text, chunk_size=settings.chunk_size, overlap=settings.chunk_overlap)
    inserted = 0
    batch: list[Document] = []

    for i, chunk in enumerate(chunks):
        tags = await tag_chunk(client, chunk, taxonomy, settings)
        embedding = await embed_text(chunk, settings)
        batch.append(
            Document(
                id=uuid.uuid4(),
                source_file=str(path),
                chunk_index=i,
                content=chunk,
                category=tags.category,
                concept_tags=tags.concept_tags,
                embedding=embedding,
            )
        )
        if len(batch) >= batch_size:
            session.add_all(batch)
            await session.commit()
            inserted += len(batch)
            print(f"  Committed {inserted} chunks from {path.name}...")
            batch = []

    if batch:
        session.add_all(batch)
        await session.commit()
        inserted += len(batch)

    return inserted


async def run_ingestion(corpus_dir: pathlib.Path, taxonomy_path: pathlib.Path) -> None:
    settings = get_settings()
    taxonomy = json.loads(taxonomy_path.read_text())
    if "_note" in taxonomy:
        del taxonomy["_note"]

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    files = list(corpus_dir.glob("**/*.txt")) + list(corpus_dir.glob("**/*.md"))
    if not files:
        print(f"No .txt or .md files found in {corpus_dir}.")
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
