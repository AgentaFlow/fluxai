"""Cache service for semantic caching."""

from typing import Optional, Dict, Any, List, Tuple
from uuid import UUID
import json
import hashlib
import redis.asyncio as redis
import structlog

from app.core.config import settings
from app.services.embeddings import embedding_service
from app.utils.vector import cosine_similarity, find_most_similar

logger = structlog.get_logger()


class CacheService:
    """Semantic cache service using Redis with embedding-based similarity."""
    
    def __init__(self):
        """Initialize cache service."""
        self.redis_client = None
        self.enabled = settings.CACHE_ENABLED
        self.semantic_enabled = settings.CACHE_SEMANTIC_ENABLED
        self.similarity_threshold = settings.CACHE_SIMILARITY_THRESHOLD
        
        # Statistics tracking
        self.stats = {
            "exact_hits": 0,
            "semantic_hits": 0,
            "misses": 0,
            "total_requests": 0,
        }
        
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
    
    def _generate_exact_cache_key(self, prompt: str, model_id: str) -> str:
        """Generate exact match cache key from prompt and model."""
        content = f"{model_id}:{prompt}"
        hash_value = hashlib.sha256(content.encode()).hexdigest()
        return f"cache:exact:{hash_value[:16]}"
    
    def _generate_semantic_key(self, model_id: str) -> str:
        """Generate Redis key for semantic cache entries list."""
        return f"cache:semantic:{model_id}:entries"
    
    def _generate_embedding_key(self, cache_id: str) -> str:
        """Generate Redis key for storing embedding."""
        return f"cache:embedding:{cache_id}"
    
    def _generate_response_key(self, cache_id: str) -> str:
        """Generate Redis key for storing response."""
        return f"cache:response:{cache_id}"
    
    async def _try_exact_match(
        self,
        prompt: str,
        model_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Try to find exact match in cache."""
        cache_key = self._generate_exact_cache_key(prompt, model_id)
        
        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                self.stats["exact_hits"] += 1
                logger.debug("Exact cache hit", cache_key=cache_key)
                result = json.loads(cached_data)
                result["cache_type"] = "exact"
                return result
        except Exception as e:
            logger.error("Error in exact match lookup", error=str(e))
        
        return None
    
    async def _try_semantic_match(
        self,
        prompt: str,
        model_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Try to find semantically similar match in cache."""
        if not self.semantic_enabled:
            return None
        
        try:
            # Generate embedding for the prompt
            query_embedding = embedding_service.generate_embedding(prompt)
            
            # Get list of all cache entry IDs for this model
            semantic_key = self._generate_semantic_key(model_id)
            cache_ids = await self.redis_client.lrange(semantic_key, 0, -1)
            
            if not cache_ids:
                return None
            
            # Fetch embeddings for all cached entries
            embeddings = []
            valid_cache_ids = []
            
            for cache_id in cache_ids:
                embedding_key = self._generate_embedding_key(cache_id)
                embedding_data = await self.redis_client.get(embedding_key)
                
                if embedding_data:
                    embedding = json.loads(embedding_data)
                    embeddings.append(embedding)
                    valid_cache_ids.append(cache_id)
            
            if not embeddings:
                return None
            
            # Find most similar embedding
            result = find_most_similar(
                query_embedding,
                embeddings,
                threshold=self.similarity_threshold,
            )
            
            if result:
                idx, similarity = result
                cache_id = valid_cache_ids[idx]
                
                # Retrieve the cached response
                response_key = self._generate_response_key(cache_id)
                response_data = await self.redis_client.get(response_key)
                
                if response_data:
                    self.stats["semantic_hits"] += 1
                    logger.info(
                        "Semantic cache hit",
                        cache_id=cache_id,
                        similarity=similarity,
                        threshold=self.similarity_threshold,
                    )
                    
                    response = json.loads(response_data)
                    response["cache_type"] = "semantic"
                    response["similarity_score"] = similarity
                    return response
            
        except Exception as e:
            logger.error("Error in semantic match lookup", error=str(e))
        
        return None
    
    async def get(
        self,
        prompt: str,
        model_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached response if available.
        
        Tries exact match first, then semantic similarity if enabled.
        
        Returns:
            Cached response dict or None if not found
        """
        if not self.is_enabled():
            return None
        
        self.stats["total_requests"] += 1
        
        # Try exact match first (faster)
        if settings.CACHE_EXACT_MATCH_FIRST:
            result = await self._try_exact_match(prompt, model_id)
            if result:
                return result
        
        # Try semantic match
        result = await self._try_semantic_match(prompt, model_id)
        if result:
            return result
        
        # Cache miss
        self.stats["misses"] += 1
        logger.debug("Cache miss", model_id=model_id)
        return None
    
    async def set(
        self,
        prompt: str,
        model_id: str,
        response: Dict[str, Any],
    ):
        """
        Cache a response with both exact and semantic matching.
        
        Stores:
        1. Exact match entry (hash-based)
        2. Semantic entry with embedding (if enabled)
        """
        if not self.is_enabled():
            return
        
        try:
            # 1. Store exact match entry
            exact_key = self._generate_exact_cache_key(prompt, model_id)
            await self.redis_client.setex(
                exact_key,
                settings.CACHE_TTL_SECONDS,
                json.dumps(response),
            )
            
            # 2. Store semantic entry if enabled
            if self.semantic_enabled:
                # Generate unique cache ID
                cache_id = hashlib.sha256(
                    f"{model_id}:{prompt}:{response.get('timestamp', '')}".encode()
                ).hexdigest()[:16]
                
                # Generate and store embedding
                embedding = embedding_service.generate_embedding(prompt)
                embedding_key = self._generate_embedding_key(cache_id)
                await self.redis_client.setex(
                    embedding_key,
                    settings.EMBEDDING_CACHE_TTL,
                    json.dumps(embedding),
                )
                
                # Store response
                response_key = self._generate_response_key(cache_id)
                await self.redis_client.setex(
                    response_key,
                    settings.CACHE_TTL_SECONDS,
                    json.dumps(response),
                )
                
                # Add to semantic entries list
                semantic_key = self._generate_semantic_key(model_id)
                await self.redis_client.lpush(semantic_key, cache_id)
                await self.redis_client.expire(semantic_key, settings.CACHE_TTL_SECONDS)
                
                logger.debug(
                    "Response cached with semantic embedding",
                    cache_id=cache_id,
                    model_id=model_id,
                    embedding_dim=len(embedding),
                )
            else:
                logger.debug(
                    "Response cached (exact match only)",
                    exact_key=exact_key,
                )
            
        except Exception as e:
            logger.error("Cache set error", error=str(e))
    
    async def get_stats(self, account_id: UUID) -> Dict[str, Any]:
        """
        Get cache statistics for an account.
        
        TODO: Implement per-account stats tracking.
        """
        total = self.stats["total_requests"]
        exact_hits = self.stats["exact_hits"]
        semantic_hits = self.stats["semantic_hits"]
        total_hits = exact_hits + semantic_hits
        
        hit_rate = total_hits / total if total > 0 else 0.0
        
        # Calculate approximate savings
        # Assuming average cost of $0.005 per request
        avg_cost_per_request = 0.005
        cost_saved = total_hits * avg_cost_per_request
        
        # Subtract embedding costs (rough estimate)
        embedding_cost = 0.0
        if self.semantic_enabled:
            # $0.0001 per 1K tokens, average prompt ~200 tokens
            embedding_cost = (semantic_hits * 200 / 1000) * 0.0001
        
        net_savings = cost_saved - embedding_cost
        
        return {
            "hit_rate": round(hit_rate, 4),
            "total_requests": total,
            "exact_hits": exact_hits,
            "semantic_hits": semantic_hits,
            "total_hits": total_hits,
            "misses": self.stats["misses"],
            "cache_size_mb": 0,  # TODO: Implement actual size tracking
            "requests_saved": total_hits,
            "cost_saved": round(cost_saved, 4),
            "embedding_cost": round(embedding_cost, 6),
            "net_savings": round(net_savings, 4),
            "tokens_saved": 0,  # TODO: Track from actual responses
            "semantic_enabled": self.semantic_enabled,
            "similarity_threshold": self.similarity_threshold,
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
            
            # Reset stats
            self.stats = {
                "exact_hits": 0,
                "semantic_hits": 0,
                "misses": 0,
                "total_requests": 0,
            }
            
            logger.info("Cache cleared", account_id=str(account_id) if account_id else "all")
        except Exception as e:
            logger.error("Cache clear error", error=str(e))


# Singleton instance
cache_service = CacheService()
