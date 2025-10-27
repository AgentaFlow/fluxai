"""Cache service for semantic caching."""

from typing import Optional, Dict, Any
from uuid import UUID
import json
import hashlib
import redis.asyncio as redis
import structlog

from app.core.config import settings

logger = structlog.get_logger()


class CacheService:
    """Semantic cache service using Redis."""
    
    def __init__(self):
        """Initialize cache service."""
        self.redis_client = None
        self.enabled = settings.CACHE_ENABLED
        
        if self.enabled:
            self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis client."""
        try:
            self.redis_client = redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
            )
            logger.info("Redis client initialized", url=settings.REDIS_URL)
        except Exception as e:
            logger.error("Failed to initialize Redis", error=str(e))
            self.enabled = False
    
    def is_enabled(self) -> bool:
        """Check if cache is enabled."""
        return self.enabled and self.redis_client is not None
    
    def _generate_cache_key(self, prompt: str, model_id: str) -> str:
        """
        Generate cache key from prompt and model.
        
        For MVP, we use exact match. 
        TODO: Implement semantic similarity with embeddings.
        """
        # Create hash of prompt + model
        content = f"{model_id}:{prompt}"
        hash_value = hashlib.sha256(content.encode()).hexdigest()
        return f"cache:exact:{hash_value[:16]}"
    
    async def get(
        self,
        prompt: str,
        model_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available.
        
        Returns None if not cached.
        """
        if not self.is_enabled():
            return None
        
        try:
            cache_key = self._generate_cache_key(prompt, model_id)
            
            # Get from Redis
            cached_data = await self.redis_client.get(cache_key)
            
            if cached_data:
                logger.debug("Cache hit", cache_key=cache_key)
                return json.loads(cached_data)
            else:
                logger.debug("Cache miss", cache_key=cache_key)
                return None
                
        except Exception as e:
            logger.error("Cache get error", error=str(e))
            return None
    
    async def set(
        self,
        prompt: str,
        model_id: str,
        response: Dict[str, Any],
    ):
        """
        Cache a response.
        """
        if not self.is_enabled():
            return
        
        try:
            cache_key = self._generate_cache_key(prompt, model_id)
            
            # Store in Redis with TTL
            await self.redis_client.setex(
                cache_key,
                settings.CACHE_TTL_SECONDS,
                json.dumps(response),
            )
            
            logger.debug(
                "Response cached",
                cache_key=cache_key,
                ttl=settings.CACHE_TTL_SECONDS,
            )
            
        except Exception as e:
            logger.error("Cache set error", error=str(e))
    
    async def get_stats(self, account_id: UUID) -> Dict[str, Any]:
        """
        Get cache statistics for an account.
        
        TODO: Implement proper stats tracking per account.
        """
        # For MVP, return placeholder stats
        return {
            "hit_rate": 0.0,
            "total_hits": 0,
            "total_misses": 0,
            "cache_size_mb": 0,
            "requests_saved": 0,
            "cost_saved": 0.0,
            "tokens_saved": 0,
        }
    
    async def clear(self, account_id: Optional[UUID] = None):
        """
        Clear cache for an account or all cache.
        
        TODO: Implement account-specific cache clearing.
        """
        if not self.is_enabled():
            return
        
        try:
            # For MVP, this clears all cache
            # TODO: Implement account-specific clearing
            await self.redis_client.flushdb()
            logger.info("Cache cleared", account_id=str(account_id) if account_id else "all")
        except Exception as e:
            logger.error("Cache clear error", error=str(e))


# Singleton instance
cache_service = CacheService()
