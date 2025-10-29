"""
OpenTelemetry Tracing Middleware

Distributed tracing for FluxAI Gateway using OpenTelemetry.
"""

from typing import Optional, Dict, Any
from contextlib import contextmanager
import os
import structlog

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace import Status, StatusCode, Span

logger = structlog.get_logger()


class TracingMiddleware:
    """
    OpenTelemetry tracing middleware for FluxAI.
    
    Provides distributed tracing across all operations:
    - Request handling
    - Bedrock API calls
    - Cache lookups
    - Embedding generation
    - Cost calculation
    """
    
    def __init__(
        self,
        service_name: str = "fluxai-gateway",
        otlp_endpoint: Optional[str] = None,
    ):
        """
        Initialize tracing middleware.
        
        Args:
            service_name: Name of the service for trace attribution
            otlp_endpoint: OTLP collector endpoint (e.g., "localhost:4317")
        """
        self.service_name = service_name
        self.otlp_endpoint = otlp_endpoint
        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None
        self.initialized = False
    
    def initialize(self):
        """Initialize OpenTelemetry tracer."""
        if self.initialized:
            return
        
        # Create resource with service name
        resource = Resource.create({
            "service.name": self.service_name,
            "service.version": "1.0.0",
        })
        
        # Create tracer provider
        self.tracer_provider = TracerProvider(resource=resource)
        # Add OTLP exporter if endpoint configured
        if self.otlp_endpoint:
            # Use TLS by default, allow insecure only if explicitly set via environment
            use_insecure = os.getenv("OTLP_INSECURE", "false").lower() == "true"
            otlp_exporter = OTLPSpanExporter(
                endpoint=self.otlp_endpoint,
                insecure=use_insecure,
            )
            span_processor = BatchSpanProcessor(otlp_exporter)
            self.tracer_provider.add_span_processor(span_processor)
            
            logger.info(
                "OTLP trace exporter configured",
                endpoint=self.otlp_endpoint,
            )
        
        # Set as global tracer provider
        trace.set_tracer_provider(self.tracer_provider)
        
        # Get tracer
        self.tracer = trace.get_tracer(__name__)
        
        self.initialized = True
        logger.info("OpenTelemetry tracing initialized", service=self.service_name)
    
    @contextmanager
    def trace_request(
        self,
        operation_name: str,
        model_id: str,
        max_tokens: int,
        routing_strategy: str = "auto",
        **attributes,
    ):
        """
        Trace a complete request operation.
        
        Args:
            operation_name: Name of the operation (e.g., "chat_completion")
            model_id: Model being used
            max_tokens: Maximum tokens to generate
            routing_strategy: Routing strategy used
            **attributes: Additional span attributes
        
        Yields:
            Span context for nested operations
        """
        if not self.initialized or not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span(operation_name) as span:
            # Set standard attributes
            span.set_attribute("model.id", model_id)
            span.set_attribute("model.max_tokens", max_tokens)
            span.set_attribute("routing.strategy", routing_strategy)
            
            # Set custom attributes
            for key, value in attributes.items():
                span.set_attribute(key, value)
            
            try:
                yield span
            except Exception as e:
                self.record_exception(span, e)
                raise
    
    @contextmanager
    def trace_bedrock_call(
        self,
        model_id: str,
        input_tokens: int,
        max_tokens: int,
        region: str = "us-east-1",
    ):
        """
        Trace a Bedrock API call.
        
        Args:
            model_id: Model being invoked
            input_tokens: Number of input tokens
            max_tokens: Maximum output tokens
            region: AWS region
        
        Yields:
            Span context
        """
        if not self.initialized or not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span("bedrock.invoke_model") as span:
            span.set_attribute("bedrock.model_id", model_id)
            span.set_attribute("bedrock.region", region)
            span.set_attribute("bedrock.input_tokens", input_tokens)
            span.set_attribute("bedrock.max_tokens", max_tokens)
            
            try:
                yield span
            except Exception as e:
                self.record_exception(span, e)
                raise
    
    @contextmanager
    def trace_cache_lookup(
        self,
        model_id: str,
        cache_type: str = "semantic",
        similarity_threshold: float = 0.95,
    ):
        """
        Trace a cache lookup operation.
        
        Args:
            model_id: Model to look up
            cache_type: Type of cache ("exact" or "semantic")
            similarity_threshold: Similarity threshold for semantic cache
        
        Yields:
            Span context
        """
        if not self.initialized or not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span("cache.lookup") as span:
            span.set_attribute("cache.type", cache_type)
            span.set_attribute("cache.model_id", model_id)
            
            if cache_type == "semantic":
                span.set_attribute("cache.similarity_threshold", similarity_threshold)
            
            try:
                yield span
            except Exception as e:
                self.record_exception(span, e)
                raise
    
    @contextmanager
    def trace_embedding_generation(
        self,
        input_tokens: int,
        model: str = "amazon.titan-embed-text-v1",
    ):
        """
        Trace embedding generation for semantic cache.
        
        Args:
            input_tokens: Number of input tokens
            model: Embedding model used
        
        Yields:
            Span context
        """
        if not self.initialized or not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span("embeddings.generate") as span:
            span.set_attribute("embeddings.model", model)
            span.set_attribute("embeddings.input_tokens", input_tokens)
            
            try:
                yield span
            except Exception as e:
                self.record_exception(span, e)
                raise
    
    @contextmanager
    def trace_cost_calculation(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        region: str = "us-east-1",
    ):
        """
        Trace cost calculation.
        
        Args:
            model_id: Model being costed
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            region: AWS region
        
        Yields:
            Span context
        """
        if not self.initialized or not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span("cost.calculate") as span:
            span.set_attribute("cost.model_id", model_id)
            span.set_attribute("cost.region", region)
            span.set_attribute("cost.input_tokens", input_tokens)
            span.set_attribute("cost.output_tokens", output_tokens)
            
            try:
                yield span
            except Exception as e:
                self.record_exception(span, e)
                raise
    
    @contextmanager
    def trace_routing_decision(
        self,
        strategy: str,
        candidates: int,
        constraints: Optional[Dict[str, Any]] = None,
    ):
        """
        Trace routing decision process.
        
        Args:
            strategy: Routing strategy ("cost", "latency", "capability", "auto")
            candidates: Number of candidate models
            constraints: Routing constraints
        
        Yields:
            Span context
        """
        if not self.initialized or not self.tracer:
            yield None
            return
        
        with self.tracer.start_as_current_span("routing.decide") as span:
            span.set_attribute("routing.strategy", strategy)
            span.set_attribute("routing.candidates", candidates)
            
            if constraints:
                for key, value in constraints.items():
                    span.set_attribute(f"routing.constraint.{key}", str(value))
            
            try:
                yield span
            except Exception as e:
                self.record_exception(span, e)
                raise
    
    def record_exception(
        self,
        span: Span,
        exception: Exception,
        attributes: Optional[Dict[str, Any]] = None,
    ):
        """
        Record an exception in a span.
        
        Args:
            span: Span to record exception in
            exception: Exception that occurred
            attributes: Additional attributes
        """
        if not span:
            return
        
        # Record exception
        span.record_exception(exception)
        
        # Set error status
        span.set_status(Status(StatusCode.ERROR, str(exception)))
        
        # Add custom attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        logger.error(
            "Exception recorded in trace",
            exception=str(exception),
            trace_id=format(span.get_span_context().trace_id, "032x"),
            span_id=format(span.get_span_context().span_id, "016x"),
        )
    
    def end_span_success(
        self,
        span: Span,
        **attributes,
    ):
        """
        End a span successfully with attributes.
        
        Args:
            span: Span to end
            **attributes: Additional attributes to record
        """
        if not span:
            return
        
        # Set success status
        span.set_status(Status(StatusCode.OK))
        
        # Add result attributes
        for key, value in attributes.items():
            span.set_attribute(key, value)
    
    def get_current_trace_id(self) -> Optional[str]:
        """
        Get current trace ID for correlation.
        
        Returns:
            Trace ID as hex string, or None if no active trace
        """
        if not self.initialized:
            return None
        
        span = trace.get_current_span()
        if span:
            trace_id = span.get_span_context().trace_id
            return format(trace_id, "032x")
        
        return None
    
    def get_current_span_id(self) -> Optional[str]:
        """
        Get current span ID for correlation.
        
        Returns:
            Span ID as hex string, or None if no active span
        """
        if not self.initialized:
            return None
        
        span = trace.get_current_span()
        if span:
            span_id = span.get_span_context().span_id
            return format(span_id, "016x")
        
        return None


# Singleton instance
tracing_middleware = TracingMiddleware()
