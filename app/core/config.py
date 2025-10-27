"""Application configuration."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Application
    APP_NAME: str = "FluxAI Gateway"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    WORKERS: int = 4
    RELOAD: bool = True
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    
    # AWS Configuration
    AWS_REGION: str = "us-east-1"
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_BEDROCK_ENDPOINT: str = ""
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://fluxai:dev_password@localhost:5432/fluxai"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    
    # Security
    SECRET_KEY: str = Field(default="change-me-in-production")
    API_KEY_HASH_ALGORITHM: str = "HS256"
    RATE_LIMIT_ENABLED: bool = True
    
    # Observability
    PROMETHEUS_ENABLED: bool = True
    PROMETHEUS_PORT: int = 9090
    OPENTELEMETRY_ENABLED: bool = True
    JAEGER_ENDPOINT: str = "http://localhost:14268/api/traces"
    
    # Cache Configuration
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600
    CACHE_SIMILARITY_THRESHOLD: float = 0.95
    
    # Cost Tracking
    ENABLE_COST_TRACKING: bool = True
    PRICING_UPDATE_INTERVAL_HOURS: int = 24


settings = Settings()
