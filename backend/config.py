from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str

    anthropic_api_key: str
    openai_api_key: str
    claude_model: str = "claude-sonnet-4-6"
    claude_retrieval_model: str = "claude-haiku-4-5-20251001"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    langfuse_public_key: str | None = None
    langfuse_secret_key: str | None = None
    langfuse_host: str = "https://cloud.langfuse.com"

    rag_top_k: int = 5
    rag_min_similarity: float = 0.7

    chunk_size: int = 512
    chunk_overlap: int = 64
    parent_chunk_size: int = 2048

    memory_session_threshold: int = 10
    memory_top_k: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
