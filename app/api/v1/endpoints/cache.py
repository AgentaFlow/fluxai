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
    """
    logger.info("Fetching cache stats", account_id=str(account.id))
    
    stats = await cache_service.get_stats(account_id=account.id)
    
    return CacheStatsResponse(
        hit_rate=stats.get("hit_rate", 0.0),
        total_hits=stats.get("total_hits", 0),
        total_misses=stats.get("total_misses", 0),
        cache_size_mb=stats.get("cache_size_mb", 0),
        savings={
            "requests_saved": stats.get("requests_saved", 0),
            "cost_saved": stats.get("cost_saved", 0.0),
            "tokens_saved": stats.get("tokens_saved", 0),
        },
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
