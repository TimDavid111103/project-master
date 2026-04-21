from openai import AsyncOpenAI

from backend.config import Settings


async def embed_text(text: str, settings: Settings) -> list[float]:
    """Return a single embedding vector for the given text."""
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=text,
        dimensions=settings.embedding_dimensions,
    )
    return response.data[0].embedding
