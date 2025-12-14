from fastapi import APIRouter

from app.api.v1 import batch

api_router = APIRouter()

# Endpoints batch para integração NestJS (stateless)
api_router.include_router(
    batch.router,
    prefix="/batch",
    tags=["batch-processing"]
)