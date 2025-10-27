"""
Prometheus Metrics Service

Comprehensive metrics collection for FluxAI Gateway with Prometheus.
"""

from typing import Optional, Dict
from uuid import UUID
from dataclasses import dataclass
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
import structlog

from app.db.session import get_db
from app.db.models import RequestMetric
from app.services.cost_calculator import cost_calculator

logger = structlog.get_logger()


@dataclass
class RequestMetrics:
    """Metrics for a single request."""
    
    model_id: str
    region: str
    client_id: str
    status: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    cost: float
    cache_hit: bool
    routing_strategy: str
    cache_type: Optional[str] = None  # "exact" or "semantic"
    error_type: Optional[str] = None


class MetricsService:
    """
    Prometheus metrics service for FluxAI.
    
    Tracks all key performance indicators:
    - Request counts and latencies
    - Token usage
    - Cost metrics
    - Cache performance
    - Model health
    - System metrics
    """
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        """Initialize metrics collectors."""
        self.initialized = False
        self.metrics: Dict = {}
        self.registry = registry or CollectorRegistry()
        self.cost_calculator = cost_calculator
    
    def initialize(self):
        """Initialize Prometheus metrics."""
        if self.initialized:
            return
        
        # Request metrics
        self.metrics["requests_total"] = Counter(
            "fluxai_requests_total",
            "Total number of requests",
            ["account_id", "model", "region", "status"],
            registry=self.registry,
        )
        
        self.metrics["request_duration"] = Histogram(
            "fluxai_request_duration_seconds",
            "Request duration in seconds",
            ["account_id", "model", "region"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
            registry=self.registry,
        )
        
        self.metrics["request_errors"] = Counter(
            "fluxai_request_errors_total",
            "Total number of errors",
            ["model", "region", "error_type"],
            registry=self.registry,
        )
        
        # Token metrics
        self.metrics["tokens_total"] = Counter(
            "fluxai_tokens_total",
            "Total number of tokens processed",
            ["account_id", "model", "region", "type"],
            registry=self.registry,
        )
        
        self.metrics["input_tokens"] = Counter(
            "fluxai_input_tokens_total",
            "Total input tokens",
            ["model", "region", "client"],
            registry=self.registry,
        )
        
        self.metrics["output_tokens"] = Counter(
            "fluxai_output_tokens_total",
            "Total output tokens",
            ["model", "region", "client"],
            registry=self.registry,
        )
        
        # Cost metrics
        self.metrics["cost_dollars_total"] = Counter(
            "fluxai_cost_dollars_total",
            "Total cost in dollars",
            ["account_id", "model", "region"],
            registry=self.registry,
        )
        
        self.metrics["cost_per_request"] = Histogram(
            "fluxai_cost_per_request_dollars",
            "Cost per request in dollars",
            ["model", "region"],
            buckets=[0.0001, 0.001, 0.01, 0.1, 1.0, 10.0],
            registry=self.registry,
        )
        
        # Cache metrics
        self.metrics["cache_hits_total"] = Counter(
            "fluxai_cache_hits_total",
            "Total cache hits",
            ["account_id", "model", "cache_type"],
            registry=self.registry,
        )
        
        self.metrics["cache_misses_total"] = Counter(
            "fluxai_cache_misses_total",
            "Total cache misses",
            ["account_id", "model"],
            registry=self.registry,
        )
        
        self.metrics["cache_hit_rate"] = Gauge(
            "fluxai_cache_hit_rate",
            "Current cache hit rate (0-1)",
            ["model"],
            registry=self.registry,
        )
        
        self.metrics["cache_savings_dollars"] = Counter(
            "fluxai_cache_savings_dollars_total",
            "Total cost savings from cache",
            ["model"],
            registry=self.registry,
        )
        
        # Model metrics
        self.metrics["model_latency"] = Histogram(
            "fluxai_model_latency_seconds",
            "Model inference latency",
            ["model", "region"],
            buckets=[0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
            registry=self.registry,
        )
        
        self.metrics["model_availability"] = Gauge(
            "fluxai_model_availability",
            "Model availability (0-1)",
            ["model", "region"],
            registry=self.registry,
        )
        
        self.metrics["model_error_rate"] = Gauge(
            "fluxai_model_error_rate",
            "Model error rate (0-1)",
            ["model", "region"],
            registry=self.registry,
        )
        
        # Routing metrics
        self.metrics["routing_strategy_total"] = Counter(
            "fluxai_routing_strategy_total",
            "Total requests by routing strategy",
            ["strategy", "model"],
            registry=self.registry,
        )
        
        # System metrics
        self.metrics["active_connections"] = Gauge(
            "fluxai_active_connections",
            "Current active connections",
            registry=self.registry,
        )
        
        self.metrics["queue_depth"] = Gauge(
            "fluxai_queue_depth",
            "Current queue depth",
            registry=self.registry,
        )
        
        self.initialized = True
        logger.info("Prometheus metrics initialized")
    
    def record_cache_hit(
        self,
        account_id: UUID,
        model_id: str,
        cache_type: str = "semantic",
    ):
        """
        Record a cache hit.
        
        Args:
            account_id: Account ID
            model_id: Model that was cached
            cache_type: Type of cache hit ("exact" or "semantic")
        """
        if self.initialized:
            self.metrics["cache_hits_total"].labels(
                account_id=str(account_id),
                model=model_id,
                cache_type=cache_type,
            ).inc()
    
    def record_cache_miss(self, account_id: UUID, model_id: str):
        """
        Record a cache miss.
        
        Args:
            account_id: Account ID
            model_id: Model that was requested
        """
        if self.initialized:
            self.metrics["cache_misses_total"].labels(
                account_id=str(account_id),
                model=model_id,
            ).inc()
    
    def record_cache_savings(
        self,
        model_id: str,
        savings_dollars: float,
    ):
        """
        Record cost savings from cache hit.
        
        Args:
            model_id: Model that was cached
            savings_dollars: Amount saved in dollars
        """
        if self.initialized:
            self.metrics["cache_savings_dollars"].labels(
                model=model_id,
            ).inc(savings_dollars)
    
    def record_error(
        self,
        model_id: str,
        region: str,
        error_type: str,
    ):
        """
        Record an error occurrence.
        
        Args:
            model_id: Model that errored
            region: AWS region
            error_type: Type of error (e.g., "ThrottlingException")
        """
        if self.initialized:
            self.metrics["request_errors"].labels(
                model=model_id,
                region=region,
                error_type=error_type,
            ).inc()
            
            logger.warning(
                "Error recorded",
                model=model_id,
                region=region,
                error_type=error_type,
            )
    
    def update_cache_hit_rate(
        self,
        model_id: str,
        hit_rate: float,
    ):
        """
        Update cache hit rate gauge.
        
        Args:
            model_id: Model to update
            hit_rate: Hit rate (0-1)
        """
        if self.initialized:
            self.metrics["cache_hit_rate"].labels(model=model_id).set(hit_rate)
    
    def update_model_availability(
        self,
        model_id: str,
        region: str,
        availability: float,
    ):
        """
        Update model availability gauge.
        
        Args:
            model_id: Model to update
            region: AWS region
            availability: Availability (0-1)
        """
        if self.initialized:
            self.metrics["model_availability"].labels(
                model=model_id,
                region=region,
            ).set(availability)
    
    def update_model_error_rate(
        self,
        model_id: str,
        region: str,
        error_rate: float,
    ):
        """
        Update model error rate gauge.
        
        Args:
            model_id: Model to update
            region: AWS region
            error_rate: Error rate (0-1)
        """
        if self.initialized:
            self.metrics["model_error_rate"].labels(
                model=model_id,
                region=region,
            ).set(error_rate)
    
    def increment_active_connections(self):
        """Increment active connections counter."""
        if self.initialized:
            self.metrics["active_connections"].inc()
    
    def decrement_active_connections(self):
        """Decrement active connections counter."""
        if self.initialized:
            self.metrics["active_connections"].dec()
    
    def set_queue_depth(self, depth: int):
        """
        Set current queue depth.
        
        Args:
            depth: Number of requests in queue
        """
        if self.initialized:
            self.metrics["queue_depth"].set(depth)
    
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
        region: str = "us-east-1",
        routing_strategy: str = "auto",
        cache_type: Optional[str] = None,
        error_message: Optional[str] = None,
        error_type: Optional[str] = None,
    ):
        """
        Record request metrics to Prometheus and database.
        
        Args:
            account_id: Account ID
            model_id: Model used
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            cost: Total cost in dollars
            latency_ms: Request latency in milliseconds
            cache_hit: Whether request was served from cache
            status: Request status ("success", "error", etc.)
            region: AWS region
            routing_strategy: Routing strategy used
            cache_type: Type of cache hit ("exact" or "semantic")
            error_message: Error message if failed
            error_type: Error type if failed
        """
        # Record to Prometheus
        if self.initialized:
            # Request count
            self.metrics["requests_total"].labels(
                account_id=str(account_id),
                model=model_id,
                region=region,
                status=status,
            ).inc()
            
            # Request duration
            self.metrics["request_duration"].labels(
                account_id=str(account_id),
                model=model_id,
                region=region,
            ).observe(latency_ms / 1000.0)
            
            # Tokens (legacy format for backward compatibility)
            self.metrics["tokens_total"].labels(
                account_id=str(account_id),
                model=model_id,
                region=region,
                type="input",
            ).inc(input_tokens)
            
            self.metrics["tokens_total"].labels(
                account_id=str(account_id),
                model=model_id,
                region=region,
                type="output",
            ).inc(output_tokens)
            
            # New token metrics
            self.metrics["input_tokens"].labels(
                model=model_id,
                region=region,
                client=str(account_id),
            ).inc(input_tokens)
            
            self.metrics["output_tokens"].labels(
                model=model_id,
                region=region,
                client=str(account_id),
            ).inc(output_tokens)
            
            # Cost
            self.metrics["cost_dollars_total"].labels(
                account_id=str(account_id),
                model=model_id,
                region=region,
            ).inc(cost)
            
            if status == "success":
                self.metrics["cost_per_request"].labels(
                    model=model_id,
                    region=region,
                ).observe(cost)
                
                # Model latency
                self.metrics["model_latency"].labels(
                    model=model_id,
                    region=region,
                ).observe(latency_ms / 1000.0)
            
            # Routing metrics
            self.metrics["routing_strategy_total"].labels(
                strategy=routing_strategy,
                model=model_id,
            ).inc()
            
            # Error metrics
            if status != "success" and error_type:
                self.record_error(model_id, region, error_type)
        
        # Store to database
        try:
            async with get_db() as db:
                total_tokens = input_tokens + output_tokens
                
                # Calculate accurate input/output costs
                cost_breakdown = self.cost_calculator.calculate_cost(
                    model_id=model_id,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    region=region,
                )
                
                metric = RequestMetric(
                    account_id=account_id,
                    model_id=model_id,
                    region=region,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    total_tokens=total_tokens,
                    input_cost=cost_breakdown.input_cost,
                    output_cost=cost_breakdown.output_cost,
                    total_cost=cost,
                    latency_ms=latency_ms,
                    cache_hit=cache_hit,
                    status=status,
                    error_message=error_message,
                )
                
                db.add(metric)
                await db.commit()
                
                logger.debug(
                    "Request metric stored",
                    model=model_id,
                    cost=cost,
                    latency_ms=latency_ms,
                )
                
        except Exception as e:
            logger.error("Failed to store request metric", error=str(e))
    
    def get_metrics(self) -> bytes:
        """
        Get Prometheus metrics in exposition format.
        
        Returns:
            Metrics in Prometheus text format
        """
        return generate_latest(self.registry)
    
    def get_content_type(self) -> str:
        """
        Get content type for Prometheus metrics.
        
        Returns:
            Content type string
        """
        return CONTENT_TYPE_LATEST


# Singleton instance
metrics_service = MetricsService()
