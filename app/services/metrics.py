"""Metrics service for Prometheus."""

from typing import Optional
from uuid import UUID
from prometheus_client import Counter, Histogram, Gauge
import structlog

from app.db.session import get_db
from app.db.models import RequestMetric
from app.services.cost_calculator import CostCalculator

logger = structlog.get_logger()


class MetricsService:
    """Prometheus metrics service."""
    def __init__(self):
        """Initialize metrics collectors."""
        self.initialized = False
        self.metrics = {}
        self.cost_calculator = CostCalculator()
    
    def initialize(self):
        """Initialize Prometheus metrics."""
        if self.initialized:
            return
        
        # Request metrics
        self.metrics["requests_total"] = Counter(
            "fluxai_requests_total",
            "Total number of requests",
            ["account_id", "model", "status"],
        )
        
        self.metrics["request_duration"] = Histogram(
            "fluxai_request_duration_seconds",
            "Request duration in seconds",
            ["account_id", "model"],
        )
        
        # Token metrics
        self.metrics["tokens_total"] = Counter(
            "fluxai_tokens_total",
            "Total number of tokens processed",
            ["account_id", "model", "type"],
        )
        
        # Cost metrics
        self.metrics["cost_dollars_total"] = Counter(
            "fluxai_cost_dollars_total",
            "Total cost in dollars",
            ["account_id", "model"],
        )
        
        # Cache metrics
        self.metrics["cache_hits_total"] = Counter(
            "fluxai_cache_hits_total",
            "Total cache hits",
            ["account_id", "model"],
        )
        
        self.metrics["cache_misses_total"] = Counter(
            "fluxai_cache_misses_total",
            "Total cache misses",
            ["account_id", "model"],
        )
        
        self.initialized = True
        logger.info("Prometheus metrics initialized")
    
    def record_cache_hit(self, account_id: UUID, model_id: str):
        """Record a cache hit."""
        if self.initialized:
            self.metrics["cache_hits_total"].labels(
                account_id=str(account_id),
                model=model_id,
            ).inc()
    
    def record_cache_miss(self, account_id: UUID, model_id: str):
        """Record a cache miss."""
        if self.initialized:
            self.metrics["cache_misses_total"].labels(
                account_id=str(account_id),
                model=model_id,
            ).inc()
    
    async def record_request(
        self,
        account_id: UUID,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        cost: float,
        latency_ms: int,
        cache_hit: bool,
        status: str,
        error_message: Optional[str] = None,
    ):
        """
        Record request metrics to Prometheus and database.
        """
        # Record to Prometheus
        if self.initialized:
            # Request count
            self.metrics["requests_total"].labels(
                account_id=str(account_id),
                model=model_id,
                status=status,
            ).inc()
            
            # Request duration
            self.metrics["request_duration"].labels(
                account_id=str(account_id),
                model=model_id,
            ).observe(latency_ms / 1000.0)
            
            # Tokens
            self.metrics["tokens_total"].labels(
                account_id=str(account_id),
                model=model_id,
                type="input",
            ).inc(input_tokens)
            
            self.metrics["tokens_total"].labels(
                account_id=str(account_id),
                model=model_id,
                type="output",
            ).inc(output_tokens)
            
            # Cost
            self.metrics["cost_dollars_total"].labels(
                account_id=str(account_id),
                model=model_id,
            ).inc(cost)
        # Store to database
        try:
            async with get_db() as db:
                total_tokens = input_tokens + output_tokens
                
                # Calculate accurate input/output costs using proper pricing ratios
                input_cost = self.cost_calculator.calculate_input_cost(model_id, input_tokens)
                output_cost = self.cost_calculator.calculate_output_cost(model_id, output_tokens)
                
                metric = RequestMetric(
                    account_id=account_id,
                    model_id=model_id,
                    region="us-east-1",  # TODO: Get from config
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    input_cost=input_cost,
                    output_cost=output_cost,
                    total_cost=cost,
                    latency_ms=latency_ms,
                    cache_hit=cache_hit,
                    status=status,
                    error_message=error_message,
                )
                
                db.add(metric)
                await db.commit()
                db.add(metric)
                await db.commit()
                
        except Exception as e:
            logger.error("Failed to store request metric", error=str(e))


# Singleton instance
metrics_service = MetricsService()
