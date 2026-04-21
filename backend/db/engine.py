from __future__ import annotations

from typing import TYPE_CHECKING, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine

_engine: AsyncEngine | None = None
_factory: async_sessionmaker | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        from backend.config import get_settings
        _engine = create_async_engine(get_settings().database_url, echo=False)
    return _engine


def _get_factory() -> async_sessionmaker:
    global _factory
    if _factory is None:
        _factory = async_sessionmaker(
            _get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _factory


async def get_engine() -> AsyncEngine:
    return _get_engine()


async def async_session_factory() -> AsyncGenerator[AsyncSession, None]:
    async with _get_factory()() as session:
        yield session


async def dispose_engine() -> None:
    global _engine, _factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _factory = None
