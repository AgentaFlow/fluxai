"""
Structured Logging Middleware

Centralized logging with trace correlation for FluxAI Gateway.
"""

from typing import Optional, Dict, Any
import structlog
from datetime import datetime

from app.middleware.tracing import tracing_middleware


class LoggingMiddleware:
    """
    Structured logging middleware with trace correlation.
    
    Features:
    - JSON-formatted logs
    - Trace ID correlation with OpenTelemetry
    - Request/response logging
    - Error tracking
    - Performance metrics
    """
    
    def __init__(self):
        """Initialize logging middleware."""
        self.logger = structlog.get_logger()
        self.initialized = False
    
    def initialize(self):
        """Configure structured logging."""
        if self.initialized:
            return
        
        # Configure structlog
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        
        self.initialized = True
        self.logger.info("Structured logging initialized")
    
    def log_request(
        self,
        client_id: str,
        request_data: Dict[str, Any],
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
    ):
        """
        Log incoming request.
        
        Args:
            client_id: Client identifier
            request_data: Request details
            trace_id: OpenTelemetry trace ID
            span_id: OpenTelemetry span ID
        """
        # Get trace IDs from context if not provided
        if not trace_id:
            trace_id = tracing_middleware.get_current_trace_id()
        if not span_id:
            span_id = tracing_middleware.get_current_span_id()
        
        log_data = {
            "event": "request_received",
            "client_id": client_id,
            "model": request_data.get("model"),
            "max_tokens": request_data.get("max_tokens"),
            "routing_strategy": request_data.get("routing_strategy", "auto"),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add trace correlation
        if trace_id:
            log_data["trace_id"] = trace_id
        if span_id:
            log_data["span_id"] = span_id
        
        self.logger.info("Request received", **log_data)
    
    def log_response(
        self,
        client_id: str,
        request_data: Dict[str, Any],
        response_data: Dict[str, Any],
        latency_ms: int,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
    ):
        """
        Log successful response.
        
        Args:
            client_id: Client identifier
            request_data: Request details
            response_data: Response details
            latency_ms: Request latency in milliseconds
            trace_id: OpenTelemetry trace ID
            span_id: OpenTelemetry span ID
        """
        # Get trace IDs from context if not provided
        if not trace_id:
            trace_id = tracing_middleware.get_current_trace_id()
        if not span_id:
            span_id = tracing_middleware.get_current_span_id()
        
        log_data = {
            "event": "request_completed",
            "client_id": client_id,
            "model": response_data.get("model"),
            "input_tokens": response_data.get("input_tokens", 0),
            "output_tokens": response_data.get("output_tokens", 0),
            "cost": response_data.get("cost", 0.0),
            "cache_hit": response_data.get("cache_hit", False),
            "cache_type": response_data.get("cache_type"),
            "latency_ms": latency_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add trace correlation
        if trace_id:
            log_data["trace_id"] = trace_id
        if span_id:
            log_data["span_id"] = span_id
        
        # Add cost savings if cache hit
        if response_data.get("cache_hit"):
            log_data["savings_dollars"] = response_data.get("savings_dollars", 0.0)
        
        self.logger.info("Request completed", **log_data)
    
    def log_error(
        self,
        client_id: str,
        error: Exception,
        request_data: Optional[Dict[str, Any]] = None,
        trace_id: Optional[str] = None,
        span_id: Optional[str] = None,
    ):
        """
        Log error occurrence.
        
        Args:
            client_id: Client identifier
            error: Exception that occurred
            request_data: Request details
            trace_id: OpenTelemetry trace ID
            span_id: OpenTelemetry span ID
        """
        # Get trace IDs from context if not provided
        if not trace_id:
            trace_id = tracing_middleware.get_current_trace_id()
        if not span_id:
            span_id = tracing_middleware.get_current_span_id()
        
        log_data = {
            "event": "request_error",
            "client_id": client_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Add request context if available
        if request_data:
            log_data["model"] = request_data.get("model")
            log_data["routing_strategy"] = request_data.get("routing_strategy", "auto")
        
        # Add trace correlation
        if trace_id:
            log_data["trace_id"] = trace_id
        if span_id:
            log_data["span_id"] = span_id
        
        self.logger.error("Request error", **log_data, exc_info=error)
    
    def log_cache_hit(
        self,
        client_id: str,
        model_id: str,
        cache_type: str,
        similarity: Optional[float] = None,
        savings_dollars: float = 0.0,
    ):
        """
        Log cache hit event.
        
        Args:
            client_id: Client identifier
            model_id: Model that was cached
            cache_type: Type of cache hit ("exact" or "semantic")
            similarity: Similarity score for semantic cache
            savings_dollars: Cost savings from cache hit
        """
        trace_id = tracing_middleware.get_current_trace_id()
        span_id = tracing_middleware.get_current_span_id()
        
        log_data = {
            "event": "cache_hit",
            "client_id": client_id,
            "model": model_id,
            "cache_type": cache_type,
            "savings_dollars": savings_dollars,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if similarity is not None:
            log_data["similarity"] = similarity
        
        if trace_id:
            log_data["trace_id"] = trace_id
        if span_id:
            log_data["span_id"] = span_id
        
        self.logger.info("Cache hit", **log_data)
    
    def log_routing_decision(
        self,
        client_id: str,
        strategy: str,
        selected_model: str,
        candidates: int,
        reason: str,
    ):
        """
        Log routing decision.
        
        Args:
            client_id: Client identifier
            strategy: Routing strategy used
            selected_model: Model that was selected
            candidates: Number of candidate models
            reason: Reason for selection
        """
        trace_id = tracing_middleware.get_current_trace_id()
        span_id = tracing_middleware.get_current_span_id()
        
        log_data = {
            "event": "routing_decision",
            "client_id": client_id,
            "strategy": strategy,
            "selected_model": selected_model,
            "candidates": candidates,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        if trace_id:
            log_data["trace_id"] = trace_id
        if span_id:
            log_data["span_id"] = span_id
        
        self.logger.info("Routing decision", **log_data)
    
    def log_model_health(
        self,
        model_id: str,
        region: str,
        availability: float,
        error_rate: float,
        avg_latency_ms: float,
    ):
        """
        Log model health metrics.
        
        Args:
            model_id: Model identifier
            region: AWS region
            availability: Model availability (0-1)
            error_rate: Error rate (0-1)
            avg_latency_ms: Average latency in milliseconds
        """
        log_data = {
            "event": "model_health",
            "model": model_id,
            "region": region,
            "availability": availability,
            "error_rate": error_rate,
            "avg_latency_ms": avg_latency_ms,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        # Health status determination
        if availability >= 0.99 and error_rate < 0.01:
            status = "healthy"
            level = "info"
        elif availability >= 0.95 and error_rate < 0.05:
            status = "degraded"
            level = "warning"
        else:
            status = "unhealthy"
            level = "error"
        
        log_data["status"] = status
        
        # Log with appropriate level
        if level == "warning":
            self.logger.warning("Model health check", **log_data)
        elif level == "error":
            self.logger.error("Model health check", **log_data)
        else:
            self.logger.info("Model health check", **log_data)


# Singleton instance
logging_middleware = LoggingMiddleware()
