# Semantic Cache Implementation Guide

## Overview

The FluxAI Gateway implements a **two-tier semantic caching system** that can reduce AWS Bedrock costs by 30-50% through intelligent response caching. The system uses both exact matching (hash-based) and semantic similarity (embedding-based) to identify and serve cached responses.

## Architecture

### Two-Tier Caching Strategy

```
Request → Exact Match → Semantic Match → Bedrock API
           (Fast O(1))   (Smart O(n))    (Expensive)
              ↓              ↓              ↓
           Cache Hit    Cache Hit      Cache Miss
           (~1ms)       (~100ms)      (~1-2s)
```

### Components

1. **Exact Match Cache** (`cache:exact:{hash}`)
   - Hash-based key generation using SHA256
   - O(1) Redis lookup
   - Sub-millisecond latency
   - Best for identical queries

2. **Semantic Match Cache** (`cache:semantic:{model_id}:entries`)
   - Embedding-based similarity search
   - Uses AWS Bedrock Titan Embeddings
   - Cosine similarity threshold: 0.95
   - Handles paraphrased/similar queries

3. **Embedding Service** (`app/services/embeddings.py`)
   - AWS Bedrock Titan Text Embeddings
   - 1536-dimensional vectors
   - ~$0.0001 per 1K tokens

4. **Vector Similarity** (`app/utils/vector.py`)
   - Cosine similarity calculation
   - NumPy-based optimized operations
   - Batch similarity computation

## How It Works

### Cache Lookup Flow

```python
async def get(prompt: str, model_id: str):
    # 1. Try exact match first (fastest)
    exact_key = sha256(model_id + prompt)
    cached = redis.get(f"cache:exact:{exact_key}")
    if cached:
        return cached  # ✓ Exact hit (~1ms)
    
    # 2. Try semantic match (smart)
    if semantic_enabled:
        # Generate embedding for query
        query_embedding = bedrock_titan_embed(prompt)
        
        # Get all cached embeddings for this model
        cache_ids = redis.lrange(f"cache:semantic:{model_id}:entries", 0, -1)
        
        # Fetch and compare embeddings
        for cache_id in cache_ids:
            cached_embedding = redis.get(f"cache:embedding:{cache_id}")
            similarity = cosine_similarity(query_embedding, cached_embedding)
            
            if similarity >= 0.95:
                response = redis.get(f"cache:response:{cache_id}")
                return response  # ✓ Semantic hit (~100ms)
    
    # 3. Cache miss - call Bedrock
    response = bedrock.invoke(prompt, model_id)
    
    # Store in both caches
    cache_response(prompt, model_id, response)
    
    return response  # ✗ Miss (~1-2s)
```

### Cache Storage Flow

```python
async def set(prompt: str, model_id: str, response: dict):
    # 1. Store exact match entry
    exact_key = sha256(model_id + prompt)
    redis.setex(f"cache:exact:{exact_key}", 3600, json.dumps(response))
    
    # 2. Store semantic entry (if enabled)
    if semantic_enabled:
        # Generate unique cache ID
        cache_id = sha256(model_id + prompt + timestamp)
        
        # Generate and store embedding
        embedding = bedrock_titan_embed(prompt)
        redis.setex(f"cache:embedding:{cache_id}", 86400, json.dumps(embedding))
        
        # Store response
        redis.setex(f"cache:response:{cache_id}", 3600, json.dumps(response))
        
        # Add to semantic entries list
        redis.lpush(f"cache:semantic:{model_id}:entries", cache_id)
        redis.expire(f"cache:semantic:{model_id}:entries", 3600)
```

## Cost Savings Analysis

### Example: Claude 3.5 Sonnet

**Without Caching:**
```python
Input: 500 tokens, Output: 1000 tokens
Input cost:  (500 / 1000) × $0.003 = $0.0015
Output cost: (1000 / 1000) × $0.015 = $0.0150
Total cost: $0.0165 per request
```

**With Semantic Caching (Cache Hit):**
```python
Embedding cost: (500 / 1000) × $0.0001 = $0.00005
Bedrock cost: $0 (cached)
Total cost: $0.00005 per request

Savings: $0.01645 per cache hit (99.7% reduction!)
```

### Monthly Savings Projection

| Scenario | Requests/Month | Cache Hit Rate | Monthly Savings |
|----------|---------------|----------------|-----------------|
| Small    | 10,000        | 30%            | $49             |
| Medium   | 100,000       | 40%            | $658            |
| Large    | 1,000,000     | 45%            | $7,425          |
| Enterprise | 10,000,000  | 50%            | $82,500         |

### Break-Even Analysis

The semantic cache breaks even when:
```
Embedding Cost < Bedrock Cost

For Claude 3.5 Sonnet:
Break-even after just 1 cache hit!
(Embedding: $0.00005 vs Bedrock: $0.0165)
```

## Configuration

### Environment Variables

```bash
# Cache Configuration
CACHE_ENABLED=true                    # Enable caching system
CACHE_TTL_SECONDS=3600               # Response cache TTL (1 hour)
CACHE_SIMILARITY_THRESHOLD=0.95      # Minimum similarity for semantic match
CACHE_SEMANTIC_ENABLED=true          # Enable semantic matching
CACHE_EXACT_MATCH_FIRST=true         # Try exact match before semantic

# Embedding Configuration
EMBEDDING_MODEL=amazon.titan-embed-text-v1  # Bedrock embedding model
EMBEDDING_DIMENSION=1536             # Embedding vector size
EMBEDDING_BATCH_SIZE=25              # Max batch size
EMBEDDING_CACHE_TTL=86400           # Embedding cache TTL (24 hours)
```

### Python Configuration

```python
from app.core.config import settings

# Access cache settings
if settings.CACHE_SEMANTIC_ENABLED:
    print(f"Semantic cache enabled with threshold: {settings.CACHE_SIMILARITY_THRESHOLD}")
```

## API Usage

### Get Cache Statistics

```bash
GET /v1/cache/stats
X-API-Key: your-api-key

Response:
{
  "hit_rate": 0.42,
  "total_requests": 10000,
  "exact_hits": 3200,
  "semantic_hits": 1000,
  "total_hits": 4200,
  "misses": 5800,
  "cache_size_mb": 512,
  "savings": {
    "requests_saved": 4200,
    "cost_saved": 69.30,
    "tokens_saved": 4200000,
    "embedding_cost": 0.21,
    "net_savings": 69.09
  },
  "semantic_enabled": true,
  "similarity_threshold": 0.95
}
```

### Clear Cache

```bash
DELETE /v1/cache
X-API-Key: your-api-key

Response:
{
  "status": "success",
  "message": "Cache cleared"
}
```

## Performance Characteristics

### Latency Profile

| Cache Type | Latency | Cost | Hit Rate |
|-----------|---------|------|----------|
| Exact Hit | ~1ms | $0 | 30-35% |
| Semantic Hit | ~100ms | $0.00005 | 10-15% |
| Miss | ~1-2s | $0.0165 | 55-60% |

### Scalability

- **10K cached entries**: ~100ms semantic search
- **100K cached entries**: ~500ms semantic search
- **1M+ entries**: Consider pgvector for vector DB

**Recommendation**: Implement pagination/limits on semantic search for large caches.

## Redis Data Structure

### Keys and Values

```
# Exact match cache
cache:exact:{hash}
  Type: String
  Value: JSON response
  TTL: 3600 seconds

# Semantic cache entries list
cache:semantic:{model_id}:entries
  Type: List
  Value: [cache_id1, cache_id2, ...]
  TTL: 3600 seconds

# Individual embeddings
cache:embedding:{cache_id}
  Type: String
  Value: JSON array of floats [0.123, -0.456, ...]
  TTL: 86400 seconds

# Individual responses
cache:response:{cache_id}
  Type: String
  Value: JSON response
  TTL: 3600 seconds
```

### Memory Usage Estimation

```python
# Per cached entry:
Exact match: ~1 KB (response JSON)
Semantic match: ~6 KB (embedding 1536 floats × 4 bytes + response)

# For 10,000 cached entries:
Exact only: ~10 MB
Semantic: ~60 MB

# For 100,000 cached entries:
Exact only: ~100 MB
Semantic: ~600 MB
```

## Implementation Files

### Core Files

1. **`app/services/cache.py`** - Main cache service
   - `CacheService` class
   - `get()` - Retrieve cached responses
   - `set()` - Store responses
   - `get_stats()` - Cache statistics

2. **`app/services/embeddings.py`** - Embedding generation
   - `EmbeddingService` class
   - `generate_embedding()` - Generate single embedding
   - `generate_embeddings_batch()` - Batch generation

3. **`app/utils/vector.py`** - Vector operations
   - `cosine_similarity()` - Calculate similarity
   - `find_most_similar()` - Find best match
   - `batch_cosine_similarity()` - Batch comparison

4. **`app/api/v1/endpoints/cache.py`** - Cache API
   - `GET /v1/cache/stats` - Statistics
   - `DELETE /v1/cache` - Clear cache

### Configuration Files

- **`app/core/config.py`** - Settings
- **`.env.example`** - Environment template
- **`requirements.txt`** - Dependencies (includes numpy)

## Testing

### Test Semantic Matching

```python
import asyncio
from app.services.cache import cache_service

async def test_semantic_cache():
    # Store a response
    await cache_service.set(
        prompt="What is machine learning?",
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        response={"content": "Machine learning is...", "tokens": 100}
    )
    
    # Try similar query (should hit semantic cache)
    result = await cache_service.get(
        prompt="Can you explain machine learning?",
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0"
    )
    
    assert result is not None
    assert result.get("cache_type") == "semantic"
    assert result.get("similarity_score") >= 0.95
    
    print(f"✓ Semantic cache hit with similarity: {result['similarity_score']}")

asyncio.run(test_semantic_cache())
```

### Load Testing

```bash
# Install dependencies
pip install locust

# Run load test
locust -f tests/load_test.py --host http://localhost:8080
```

## Optimization Tips

### 1. Tune Similarity Threshold

```python
# Higher threshold (0.98) = More exact matches, fewer false positives
CACHE_SIMILARITY_THRESHOLD=0.98

# Lower threshold (0.90) = More hits, but may return less relevant responses
CACHE_SIMILARITY_THRESHOLD=0.90

# Recommended: 0.95 (good balance)
```

### 2. Limit Semantic Search Scope

```python
# Only search recent N entries
cache_ids = await redis.lrange(semantic_key, 0, 100)  # Top 100 only
```

### 3. Use Exact Match First

```python
# Always try exact match before semantic (faster)
CACHE_EXACT_MATCH_FIRST=true
```

### 4. Adjust TTLs

```python
# Shorter TTL for responses (1 hour) to keep cache fresh
CACHE_TTL_SECONDS=3600

# Longer TTL for embeddings (24 hours) to reduce embedding costs
EMBEDDING_CACHE_TTL=86400
```

### 5. Consider pgvector for Scale

For >100K cached entries, migrate to PostgreSQL with pgvector:

```sql
CREATE EXTENSION vector;

CREATE TABLE cache_embeddings (
  id TEXT PRIMARY KEY,
  model_id TEXT NOT NULL,
  embedding vector(1536),
  response JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON cache_embeddings USING ivfflat (embedding vector_cosine_ops);
```

## Monitoring

### Key Metrics to Track

1. **Cache Hit Rate** - Target: >40%
2. **Semantic Hit Rate** - Target: 10-15%
3. **Average Latency** - Target: <200ms
4. **Cost Savings** - Target: >30%
5. **Redis Memory** - Monitor growth

### Prometheus Metrics

```python
from prometheus_client import Counter, Histogram

cache_hits = Counter(
    'fluxai_cache_hits_total',
    'Total cache hits',
    ['cache_type', 'model']
)

cache_latency = Histogram(
    'fluxai_cache_latency_seconds',
    'Cache lookup latency',
    ['cache_type']
)
```

## Troubleshooting

### Issue: Low Cache Hit Rate

**Causes:**
- TTL too short
- Threshold too high
- Not enough traffic variety

**Solutions:**
- Increase `CACHE_TTL_SECONDS`
- Lower `CACHE_SIMILARITY_THRESHOLD` to 0.90
- Monitor with `GET /v1/cache/stats`

### Issue: High Latency on Semantic Match

**Causes:**
- Too many cached entries
- Inefficient similarity search

**Solutions:**
- Limit search scope: `lrange(key, 0, 100)`
- Implement pagination
- Consider pgvector for >100K entries

### Issue: Redis Memory Growth

**Causes:**
- No TTL on keys
- Too many cached entries

**Solutions:**
- Verify TTL is set: `redis-cli TTL cache:exact:{key}`
- Implement LRU eviction: `maxmemory-policy allkeys-lru`
- Clear old entries: `DELETE /v1/cache`

## Future Enhancements

### Planned Features

1. **Per-Account Cache Isolation**
   - Separate cache namespaces per account
   - Account-specific statistics

2. **Advanced Vector DB Integration**
   - Pinecone or Weaviate for large-scale similarity search
   - Sub-millisecond semantic matching

3. **Cache Warming**
   - Pre-populate cache with common queries
   - Improved hit rates for new deployments

4. **Smart TTL Adjustment**
   - Increase TTL for frequently accessed entries
   - Decrease TTL for rarely used entries

5. **Multi-Model Caching**
   - Cache across similar models
   - Fallback to cheaper model if cached

## Resources

- [AWS Bedrock Titan Embeddings](https://docs.aws.amazon.com/bedrock/latest/userguide/titan-embedding-models.html)
- [Redis Commands](https://redis.io/commands)
- [Cosine Similarity Explained](https://en.wikipedia.org/wiki/Cosine_similarity)
- [pgvector Documentation](https://github.com/pgvector/pgvector)

## Support

For questions or issues:
- GitHub Issues: https://github.com/yourusername/fluxai/issues
- Documentation: See `fluxai-technical-spec.md`
- Email: support@fluxai.dev

---

**Last Updated**: January 15, 2025  
**Version**: 1.0  
**Status**: Production Ready
