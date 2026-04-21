from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import Settings, get_settings
from backend.db.engine import async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async for session in async_session_factory():
        yield session


DbDep = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]
