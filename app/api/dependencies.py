"""API dependencies."""

import hashlib
from typing import Optional
from fastapi import Header, HTTPException, status
from fastapi.security import APIKeyHeader
import structlog

from app.db.session import get_db
from app.db.models import Account, APIKey
from app.core.config import settings

logger = structlog.get_logger()

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_account(
    x_api_key: Optional[str] = Header(default=None),
) -> Account:
    """
    Validate API key and return associated account.
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    
    # Hash the API key
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    
    # Query database for API key
    async with get_db() as db:
        # TODO: Implement actual database query
        # For now, return a mock account
        logger.warning("Using mock authentication - implement database query")
        
        # Mock account for development
        from uuid import uuid4
        account = Account(
            id=uuid4(),
            name="Development Account",
            aws_account_id="123456789012",
        )
        
        return account


async def rate_limiter(
    account: Account = None,
) -> None:
    """
    Rate limiting middleware.
    """
    if not settings.RATE_LIMIT_ENABLED:
        return
    
    # TODO: Implement rate limiting with Redis
    logger.debug("Rate limiting check", account_id=str(account.id) if account else None)
    pass
