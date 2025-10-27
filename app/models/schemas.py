"""Pydantic schemas for API requests and responses."""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# Request Schemas
class Message(BaseModel):
    """Chat message."""
    role: str = Field(..., description="Role: user, assistant, or system")
    content: str = Field(..., description="Message content")


class InvokeRequest(BaseModel):
    """Request to invoke a Bedrock model."""
    model: str = Field(default="auto", description="Model ID or 'auto' for routing")
    messages: List[Message] = Field(..., description="Chat messages")
    max_tokens: int = Field(default=1000, ge=1, le=100000)
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    routing_hints: Optional[Dict[str, Any]] = Field(default=None)


class BatchInvokeRequest(BaseModel):
    """Batch request to invoke multiple models."""
    requests: List[InvokeRequest]
    routing_strategy: str = Field(default="cost-optimized")


# Response Schemas
class TokenUsage(BaseModel):
    """Token usage information."""
    input_tokens: int
    output_tokens: int
    total_tokens: int


class CostBreakdown(BaseModel):
    """Cost breakdown."""
    input: float
    output: float
    total: float


class ResponseMetadata(BaseModel):
    """Response metadata."""
    latency_ms: int
    cache_hit: bool
    region: str
    routing_strategy: str


class InvokeResponse(BaseModel):
    """Response from model invocation."""
    id: str
    model_used: str
    created: int
    content: str
    usage: TokenUsage
    cost: CostBreakdown
    metadata: ResponseMetadata


class BatchInvokeResult(BaseModel):
    """Single batch result."""
    id: str
    status: str
    response: Optional[InvokeResponse] = None
    error: Optional[str] = None


class BatchInvokeResponse(BaseModel):
    """Response from batch invocation."""
    batch_id: str
    status: str
    results: List[BatchInvokeResult]
    total_cost: float
    execution_time_ms: int


# Analytics Schemas
class CostBreakdownItem(BaseModel):
    """Cost breakdown by dimension."""
    model_id: str
    cost: float
    requests: int
    percentage: float


class CostForecast(BaseModel):
    """Cost forecast."""
    projected_monthly_cost: float
    confidence: float


class CostAnalyticsResponse(BaseModel):
    """Cost analytics response."""
    period: Dict[str, datetime]
    total_cost: float
    total_requests: int
    total_tokens: int
    breakdown: List[CostBreakdownItem]
    forecast: CostForecast


# Model Health Schemas
class ModelHealth(BaseModel):
    """Model health status."""
    model_id: str
    status: str
    availability: float
    p95_latency_ms: int
    error_rate: float
    regions: List[str]


class ModelHealthResponse(BaseModel):
    """Model health response."""
    timestamp: Optional[datetime]
    models: List[ModelHealth]


# Cache Schemas
class CacheSavings(BaseModel):
    """Cache savings information."""
    requests_saved: int
    cost_saved: float
    tokens_saved: int
    embedding_cost: Optional[float] = Field(default=0.0)
    net_savings: Optional[float] = Field(default=0.0)


class CacheStatsResponse(BaseModel):
    """Cache statistics response."""
    hit_rate: float
    total_requests: int
    exact_hits: int
    semantic_hits: int
    total_hits: int
    misses: int
    cache_size_mb: int
    savings: CacheSavings
    semantic_enabled: bool
    similarity_threshold: float
