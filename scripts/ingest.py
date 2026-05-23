"""Ingest documents from the corpus/ folder into the vector database.

Usage:
    python scripts/ingest.py

Reads every .txt and .md file in corpus/, splits each into chunks,
embeds them with OpenAI, and upserts them into the documents table.
Existing documents for the same source file are deleted first.
"""
import asyncio
import sys
from pathlib import Path

from openai import AsyncOpenAI
from sqlalchemy import delete, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.config import get_settings
from backend.db.models import Document

CORPUS_DIR = Path(__file__).resolve().parents[1] / "corpus"
SUPPORTED_EXTENSIONS = {".txt", ".md"}


def _split_into_chunks(text: str, max_chars: int) -> list[str]:
    """Split text at paragraph boundaries so each chunk is under max_chars."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        return [text.strip()] if text.strip() else []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        if current and current_len + len(para) + 2 > max_chars:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para) + 2

    if current:
        chunks.append("\n\n".join(current))

    return chunks


async def embed_texts(texts: list[str], client: AsyncOpenAI, settings) -> list[list[float]]:
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=texts,
        dimensions=settings.embedding_dimensions,
    )
    return [item.embedding for item in sorted(response.data, key=lambda x: x.index)]


async def ingest_file(
    path: Path,
    session: AsyncSession,
    openai_client: AsyncOpenAI,
    settings,
) -> int:
    source_file = path.name
    text = path.read_text(encoding="utf-8")
    max_chars = settings.chunk_size * 4  # ~4 chars per token

    chunks = _split_into_chunks(text, max_chars)
    if not chunks:
        print(f"  {source_file}: skipped (empty)")
        return 0

    # Remove existing documents for this source file
    await session.execute(
        delete(Document).where(Document.source_file == source_file)
    )

    # Embed all chunks in a single API call
    embeddings = await embed_texts(chunks, openai_client, settings)

    for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        doc = Document(
            source_file=source_file,
            chunk_index=idx,
            content=chunk,
            embedding=embedding,
        )
        session.add(doc)

    await session.commit()
    print(f"  {source_file}: {len(chunks)} chunks ingested")
    return len(chunks)


async def main() -> None:
    settings = get_settings()

    files = [
        f for f in sorted(CORPUS_DIR.iterdir())
        if f.is_file() and f.suffix in SUPPORTED_EXTENSIONS
    ]

    if not files:
        print(f"No .txt or .md files found in {CORPUS_DIR}")
        return

    print(f"Found {len(files)} file(s) in corpus/\n")

    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

    total = 0
    async with async_session() as session:
        for file_path in files:
            total += await ingest_file(file_path, session, openai_client, settings)

    await engine.dispose()
    print(f"\nDone. {total} total chunks ingested.")


if __name__ == "__main__":
    asyncio.run(main())
