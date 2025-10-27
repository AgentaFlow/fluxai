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
    OTLP_ENDPOINT: str = "localhost:4317"  # OpenTelemetry Collector endpoint
    JAEGER_ENDPOINT: str = "http://localhost:14268/api/traces"
    
    # Logging
    LOG_FORMAT: str = "json"  # "json" or "text"
    LOG_OUTPUT: str = "stdout"  # "stdout" or "file"
    LOG_FILE_PATH: str = "/var/log/fluxai/gateway.log"
    CLOUDWATCH_LOG_GROUP: str = "fluxai-gateway"
    CLOUDWATCH_LOG_STREAM: str = "gateway"
    
    # Cache Configuration
    CACHE_ENABLED: bool = True
    CACHE_TTL_SECONDS: int = 3600
    CACHE_SIMILARITY_THRESHOLD: float = 0.95
    CACHE_SEMANTIC_ENABLED: bool = True  # Enable semantic caching with embeddings
    CACHE_EXACT_MATCH_FIRST: bool = True  # Try exact match before semantic
    
    # Embedding Configuration
    EMBEDDING_MODEL: str = "amazon.titan-embed-text-v1"  # Bedrock Titan Embeddings
    EMBEDDING_DIMENSION: int = 1536  # Titan embeddings dimension
    EMBEDDING_BATCH_SIZE: int = 25  # Max batch size for Bedrock
    EMBEDDING_CACHE_TTL: int = 86400  # Cache embeddings for 24 hours
    
    # Cost Tracking
    ENABLE_COST_TRACKING: bool = True
    PRICING_UPDATE_INTERVAL_HOURS: int = 24


settings = Settings()
