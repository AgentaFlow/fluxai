"""Models API endpoints."""

from fastapi import APIRouter, Depends
import structlog

from app.api.dependencies import get_current_account
from app.models.schemas import ModelHealthResponse
from app.db.models import Account

router = APIRouter()
logger = structlog.get_logger()


@router.get("/health", response_model=ModelHealthResponse)
async def get_model_health(
    account: Account = Depends(get_current_account),
):
    """
    Get health status of all Bedrock models.
    """
    logger.info("Fetching model health", account_id=str(account.id))
    
    # TODO: Implement model health tracking
    return ModelHealthResponse(
        timestamp=None,
        models=[],
    )
