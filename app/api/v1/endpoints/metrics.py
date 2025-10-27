"""
Metrics API Endpoints

Prometheus metrics exposure for FluxAI Gateway.
"""

from fastapi import APIRouter, Response
from app.services.metrics import metrics_service

router = APIRouter()


@router.get("/metrics")
async def get_metrics():
    """
    Expose Prometheus metrics.
    
    Returns metrics in Prometheus text exposition format.
    This endpoint is designed to be scraped by Prometheus.
    
    Returns:
        Response with Prometheus metrics
    """
    metrics_data = metrics_service.get_metrics()
    content_type = metrics_service.get_content_type()
    
    return Response(
        content=metrics_data,
        media_type=content_type,
    )


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "service": "fluxai-gateway",
        "metrics_enabled": metrics_service.initialized,
    }
