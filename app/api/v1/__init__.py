"""API v1 routes."""

from fastapi import APIRouter
from app.api.v1.endpoints import bedrock, analytics, models, cache

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(bedrock.router, prefix="/bedrock", tags=["bedrock"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(models.router, prefix="/models", tags=["models"])
api_router.include_router(cache.router, prefix="/cache", tags=["cache"])
