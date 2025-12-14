from fastapi import APIRouter

from app.api.v1.endpoints import content, sources, analytics, user_preferences

api_router = APIRouter()

api_router.include_router(
    content.router,
    prefix="/content",
    tags=["content"]
)

api_router.include_router(
    sources.router,
    prefix="/sources",
    tags=["sources"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)

api_router.include_router(
    user_preferences.router,
    prefix="/users",
    tags=["users"]
)