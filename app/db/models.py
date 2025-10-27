"""Database models."""

from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Account(Base):
    """Account model."""
    
    __tablename__ = "accounts"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    aws_account_id = Column(String(12))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    api_keys = relationship("APIKey", back_populates="account")
    request_metrics = relationship("RequestMetric", back_populates="account")


class APIKey(Base):
    """API Key model."""
    
    __tablename__ = "api_keys"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id"))
    key_hash = Column(String(64), nullable=False, unique=True)
    key_prefix = Column(String(16), nullable=False)
    name = Column(String(255))
    scopes = Column(JSONB, default=[])
    rate_limit_rpm = Column(Integer, default=1000)
    rate_limit_tpm = Column(Integer, default=100000)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime)
    expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    account = relationship("Account", back_populates="api_keys")


class RequestMetric(Base):
    """Request metrics model."""
    
    __tablename__ = "request_metrics"
    
    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id = Column(PGUUID(as_uuid=True), ForeignKey("accounts.id"))
    api_key_id = Column(PGUUID(as_uuid=True), ForeignKey("api_keys.id"))
    
    request_id = Column(String(64), unique=True)
    trace_id = Column(String(64))
    
    model_id = Column(String(255), nullable=False)
    region = Column(String(32), nullable=False)
    routing_strategy = Column(String(32))
    
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    latency_ms = Column(Integer, nullable=False)
    
    input_tokens = Column(Integer, nullable=False)
    output_tokens = Column(Integer, nullable=False)
    total_tokens = Column(Integer, nullable=False)
    
    input_cost = Column(DECIMAL(10, 6), nullable=False)
    output_cost = Column(DECIMAL(10, 6), nullable=False)
    total_cost = Column(DECIMAL(10, 6), nullable=False)
    
    cache_hit = Column(Boolean, default=False)
    status = Column(String(32), nullable=False)
    error_message = Column(Text)
    
    metadata = Column(JSONB, default={})
    
    # Relationships
    account = relationship("Account", back_populates="request_metrics")


class ModelPricing(Base):
    """Model pricing model."""
    
    __tablename__ = "model_pricing"
    
    id = Column(Integer, primary_key=True)
    model_id = Column(String(255), nullable=False)
    region = Column(String(32), nullable=False)
    input_per_1k = Column(DECIMAL(10, 6), nullable=False)
    output_per_1k = Column(DECIMAL(10, 6), nullable=False)
    effective_date = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
