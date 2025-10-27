"""Cache API endpoints."""

from fastapi import APIRouter, Depends
import structlog

from app.api.dependencies import get_current_account
from app.models.schemas import CacheStatsResponse
from app.services.cache import cache_service
from app.db.models import Account

router = APIRouter()
logger = structlog.get_logger()


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    account: Account = Depends(get_current_account),
):
    """
    Get cache statistics for the account.
    
    Returns statistics including:
    - Hit rates (exact and semantic)
    - Cost savings breakdown
    - Semantic cache configuration
    """
    logger.info("Fetching cache stats", account_id=str(account.id))
    
    stats = await cache_service.get_stats(account_id=account.id)
    
    return CacheStatsResponse(
        hit_rate=stats.get("hit_rate", 0.0),
        total_requests=stats.get("total_requests", 0),
        exact_hits=stats.get("exact_hits", 0),
        semantic_hits=stats.get("semantic_hits", 0),
        total_hits=stats.get("total_hits", 0),
        misses=stats.get("misses", 0),
        cache_size_mb=stats.get("cache_size_mb", 0),
        savings={
            "requests_saved": stats.get("requests_saved", 0),
            "cost_saved": stats.get("cost_saved", 0.0),
            "tokens_saved": stats.get("tokens_saved", 0),
            "embedding_cost": stats.get("embedding_cost", 0.0),
            "net_savings": stats.get("net_savings", 0.0),
        },
        semantic_enabled=stats.get("semantic_enabled", False),
        similarity_threshold=stats.get("similarity_threshold", 0.95),
    )


@router.delete("/")
async def clear_cache(
    account: Account = Depends(get_current_account),
):
    """
    Clear cache for the account (admin only).
    """
    logger.info("Clearing cache", account_id=str(account.id))
    
    # TODO: Add admin check
    await cache_service.clear(account_id=account.id)
    
    return {"status": "success", "message": "Cache cleared"}
