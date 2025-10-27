"""Dashboard configuration."""

import os
from dataclasses import dataclass


@dataclass
class DashboardConfig:
    """Configuration for FluxAI dashboard."""
    
    # Prometheus
    prometheus_url: str = os.getenv(
        "PROMETHEUS_URL",
        "http://localhost:9090",
    )
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://fluxai:dev_password@localhost:5432/fluxai",
    )
    
    # Dashboard settings
    auto_refresh: bool = os.getenv("AUTO_REFRESH", "true").lower() == "true"
    refresh_interval: int = int(os.getenv("REFRESH_INTERVAL", "30"))
    
    # Jaeger (for tracing)
    jaeger_url: str = os.getenv(
        "JAEGER_URL",
        "http://localhost:16686",
    )
