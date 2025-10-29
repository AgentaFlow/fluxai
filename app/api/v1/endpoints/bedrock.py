"""Bedrock API endpoints."""

import time
from typing import Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from fastapi.responses import StreamingResponse
import structlog

from app.api.dependencies import get_current_account, rate_limiter
from app.models.schemas import (
    InvokeRequest,
    InvokeResponse,
    BatchInvokeRequest,
    BatchInvokeResponse,
)
from app.services.bedrock_client import bedrock_service
from app.services.cost_calculator import cost_calculator
from app.services.cache import cache_service
from app.services.metrics import metrics_service
from app.db.models import Account

router = APIRouter()
logger = structlog.get_logger()


@router.post("/invoke", response_model=InvokeResponse)
async def invoke_model(
    request: InvokeRequest,
    account: Account = Depends(get_current_account),
    x_routing_strategy: Optional[str] = Header(default="cost-optimized"),
    x_enable_cache: Optional[bool] = Header(default=True),
    x_max_cost: Optional[float] = Header(default=None),
    _rate_limit: None = Depends(rate_limiter),
):
    """
    Invoke a Bedrock model with cost optimization.
    
    This endpoint routes requests to AWS Bedrock models with:
    - Intelligent routing (cost-optimized, low-latency, capability-based)
    - Semantic caching for cost reduction
    - Real-time cost tracking
    - Comprehensive observability
    """
    start_time = time.time()
    request_id = f"req_{int(time.time() * 1000)}"
    
    logger.info(
        "Processing invoke request",
        request_id=request_id,
        account_id=str(account.id),
        model=request.model,
        routing_strategy=x_routing_strategy,
        cache_enabled=x_enable_cache,
    )
    
    # Validate messages list is not empty
    if not request.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Messages list cannot be empty",
        )
    
    try:
        # Check cache if enabled
        cache_hit = False
        cached_response = None
        
        if x_enable_cache and cache_service.is_enabled():
            prompt = request.messages[-1].content if request.messages else ""
            cached_response = await cache_service.get(
                prompt=prompt,
                model_id=request.model,
            )
            
            if cached_response:
                cache_hit = True
                logger.info("Cache hit", request_id=request_id)
                metrics_service.record_cache_hit(account.id, request.model)
            else:
                metrics_service.record_cache_miss(account.id, request.model)
        
        # If not cached, invoke Bedrock
        if not cache_hit:
            # Select model based on routing strategy
            model_id = await bedrock_service.select_model(
                request=request,
                strategy=x_routing_strategy,
                max_cost=x_max_cost,
            )
            
            # Invoke Bedrock
            bedrock_response = await bedrock_service.invoke(
                model_id=model_id,
                messages=request.messages,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
            )
            # Cache the response
            if x_enable_cache and cache_service.is_enabled():
                prompt = request.messages[-1].content if request.messages else ""
                await cache_service.set(
                    prompt=prompt,
                    model_id=model_id,
                    response=bedrock_response,
                )
            
            response_data = bedrock_response
        else:
            response_data = cached_response
        
        # Calculate cost
        cost_breakdown = cost_calculator.calculate(
            model_id=response_data["model_id"],
            input_tokens=response_data["usage"]["input_tokens"],
            output_tokens=response_data["usage"]["output_tokens"],
        )
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Record metrics
        await metrics_service.record_request(
            account_id=account.id,
            model_id=response_data["model_id"],
            input_tokens=response_data["usage"]["input_tokens"],
            output_tokens=response_data["usage"]["output_tokens"],
            cost=cost_breakdown["total"],
            latency_ms=latency_ms,
            cache_hit=cache_hit,
            status="success",
        )
        
        # Build response
        return InvokeResponse(
            id=request_id,
            model_used=response_data["model_id"],
            created=int(time.time()),
            content=response_data["content"],
            usage=response_data["usage"],
            cost={
                "input": cost_breakdown["input"],
                "output": cost_breakdown["output"],
                "total": cost_breakdown["total"],
            },
            metadata={
                "latency_ms": latency_ms,
                "cache_hit": cache_hit,
                "region": "us-east-1",  # TODO: Get from config
                "routing_strategy": x_routing_strategy,
            },
        )
        
    except Exception as e:
        logger.error(
            "Error processing invoke request",
            request_id=request_id,
            error=str(e),
            exc_info=True,
        )
        
        # Record error metrics
        await metrics_service.record_request(
            account_id=account.id,
            model_id=request.model or "unknown",
            input_tokens=0,
            output_tokens=0,
            cost=0.0,
            latency_ms=int((time.time() - start_time) * 1000),
            cache_hit=False,
            status="error",
            error_message=str(e),
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post("/invoke/stream")
async def invoke_model_stream(
    request: InvokeRequest,
    account: Account = Depends(get_current_account),
    x_routing_strategy: Optional[str] = Header(default="cost-optimized"),
    _rate_limit: None = Depends(rate_limiter),
):
    """
    Invoke a Bedrock model with streaming response.
    
    Returns Server-Sent Events (SSE) stream.
    """
    # TODO: Implement streaming
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Streaming not yet implemented",
    )


@router.post("/batch", response_model=BatchInvokeResponse)
async def batch_invoke(
    request: BatchInvokeRequest,
    account: Account = Depends(get_current_account),
    _rate_limit: None = Depends(rate_limiter),
):
    """
    Process multiple Bedrock requests in a batch.
    """
    # TODO: Implement batch processing
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Batch processing not yet implemented",
    )
