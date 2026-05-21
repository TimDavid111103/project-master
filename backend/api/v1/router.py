from fastapi import APIRouter

from backend.api.v1.endpoints.projects import router as projects_router
from backend.api.v1.endpoints.session import router as session_router

v1_router = APIRouter(prefix="/api/v1")
v1_router.include_router(session_router)
v1_router.include_router(projects_router)
