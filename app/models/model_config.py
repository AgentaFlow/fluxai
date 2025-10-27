"""Model configurations and capabilities for AWS Bedrock models."""

from dataclasses import dataclass, field
from typing import List, Dict
from enum import Enum


class ModelProvider(Enum):
    """Model providers."""
    ANTHROPIC = "anthropic"
    META = "meta"
    AMAZON = "amazon"
    MISTRAL = "mistral"


@dataclass
class ModelPricing:
    """Model pricing information."""
    input_per_1k: float  # USD per 1K input tokens
    output_per_1k: float  # USD per 1K output tokens
    region: str = "us-east-1"
    effective_date: str = "2025-10-01"


@dataclass
class ModelConfig:
    """
    Model configuration including capabilities and pricing.
    """
    model_id: str
    provider: ModelProvider
    display_name: str
    max_context_length: int
    supports_vision: bool = False
    supports_function_calling: bool = False
    supports_streaming: bool = True
    regions: List[str] = field(default_factory=lambda: ["us-east-1"])
    pricing: ModelPricing = None
    
    # Performance characteristics (defaults)
    typical_latency_ms: int = 1500
    quality_tier: str = "standard"  # basic, standard, premium
    

# AWS Bedrock Model Catalog (as of October 2025)
BEDROCK_MODELS: Dict[str, ModelConfig] = {
    # Anthropic Claude Models
    "anthropic.claude-3-5-sonnet-20241022-v2:0": ModelConfig(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude 3.5 Sonnet v2",
        max_context_length=200000,
        supports_vision=True,
        supports_function_calling=True,
        supports_streaming=True,
        regions=["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"],
        pricing=ModelPricing(
            input_per_1k=0.003,
            output_per_1k=0.015,
        ),
        typical_latency_ms=1200,
        quality_tier="premium",
    ),
    
    "anthropic.claude-3-5-haiku-20241022-v1:0": ModelConfig(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude 3.5 Haiku",
        max_context_length=200000,
        supports_vision=False,
        supports_function_calling=True,
        supports_streaming=True,
        regions=["us-east-1", "us-west-2", "eu-west-1"],
        pricing=ModelPricing(
            input_per_1k=0.001,
            output_per_1k=0.005,
        ),
        typical_latency_ms=800,
        quality_tier="standard",
    ),
    
    "anthropic.claude-3-opus-20240229-v1:0": ModelConfig(
        model_id="anthropic.claude-3-opus-20240229-v1:0",
        provider=ModelProvider.ANTHROPIC,
        display_name="Claude 3 Opus",
        max_context_length=200000,
        supports_vision=True,
        supports_function_calling=True,
        supports_streaming=True,
        regions=["us-east-1", "us-west-2"],
        pricing=ModelPricing(
            input_per_1k=0.015,
            output_per_1k=0.075,
        ),
        typical_latency_ms=2000,
        quality_tier="premium",
    ),
    
    # Meta Llama Models
    "meta.llama3-70b-instruct-v1:0": ModelConfig(
        model_id="meta.llama3-70b-instruct-v1:0",
        provider=ModelProvider.META,
        display_name="Llama 3 70B Instruct",
        max_context_length=8192,
        supports_vision=False,
        supports_function_calling=False,
        supports_streaming=True,
        regions=["us-east-1", "us-west-2", "eu-west-1"],
        pricing=ModelPricing(
            input_per_1k=0.00195,
            output_per_1k=0.00256,
        ),
        typical_latency_ms=1800,
        quality_tier="standard",
    ),
    
    "meta.llama3-8b-instruct-v1:0": ModelConfig(
        model_id="meta.llama3-8b-instruct-v1:0",
        provider=ModelProvider.META,
        display_name="Llama 3 8B Instruct",
        max_context_length=8192,
        supports_vision=False,
        supports_function_calling=False,
        supports_streaming=True,
        regions=["us-east-1", "us-west-2", "eu-west-1"],
        pricing=ModelPricing(
            input_per_1k=0.00030,
            output_per_1k=0.00060,
        ),
        typical_latency_ms=600,
        quality_tier="basic",
    ),
    
    # Amazon Titan Models
    "amazon.titan-text-express-v1": ModelConfig(
        model_id="amazon.titan-text-express-v1",
        provider=ModelProvider.AMAZON,
        display_name="Titan Text Express",
        max_context_length=8192,
        supports_vision=False,
        supports_function_calling=False,
        supports_streaming=True,
        regions=["us-east-1", "us-west-2", "eu-west-1", "ap-northeast-1"],
        pricing=ModelPricing(
            input_per_1k=0.0002,
            output_per_1k=0.0006,
        ),
        typical_latency_ms=700,
        quality_tier="basic",
    ),
    
    "amazon.titan-text-lite-v1": ModelConfig(
        model_id="amazon.titan-text-lite-v1",
        provider=ModelProvider.AMAZON,
        display_name="Titan Text Lite",
        max_context_length=4096,
        supports_vision=False,
        supports_function_calling=False,
        supports_streaming=True,
        regions=["us-east-1", "us-west-2", "eu-west-1"],
        pricing=ModelPricing(
            input_per_1k=0.00015,
            output_per_1k=0.0002,
        ),
        typical_latency_ms=500,
        quality_tier="basic",
    ),
    
    # Mistral Models
    "mistral.mistral-7b-instruct-v0:2": ModelConfig(
        model_id="mistral.mistral-7b-instruct-v0:2",
        provider=ModelProvider.MISTRAL,
        display_name="Mistral 7B Instruct",
        max_context_length=32000,
        supports_vision=False,
        supports_function_calling=False,
        supports_streaming=True,
        regions=["us-east-1", "us-west-2", "eu-west-1"],
        pricing=ModelPricing(
            input_per_1k=0.00015,
            output_per_1k=0.0002,
        ),
        typical_latency_ms=900,
        quality_tier="standard",
    ),
    
    "mistral.mixtral-8x7b-instruct-v0:1": ModelConfig(
        model_id="mistral.mixtral-8x7b-instruct-v0:1",
        provider=ModelProvider.MISTRAL,
        display_name="Mixtral 8x7B Instruct",
        max_context_length=32000,
        supports_vision=False,
        supports_function_calling=False,
        supports_streaming=True,
        regions=["us-east-1", "us-west-2", "eu-west-1"],
        pricing=ModelPricing(
            input_per_1k=0.00045,
            output_per_1k=0.0007,
        ),
        typical_latency_ms=1500,
        quality_tier="standard",
    ),
}


# Default model configurations by use case
DEFAULT_MODELS = {
    "cost-optimized": "amazon.titan-text-lite-v1",
    "balanced": "anthropic.claude-3-5-haiku-20241022-v1:0",
    "high-quality": "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "low-latency": "meta.llama3-8b-instruct-v1:0",
    "vision": "anthropic.claude-3-5-sonnet-20241022-v2:0",
}


def get_model_config(model_id: str) -> ModelConfig:
    """Get model configuration by ID."""
    if model_id not in BEDROCK_MODELS:
        raise ValueError(f"Unknown model ID: {model_id}")
    return BEDROCK_MODELS[model_id]


def get_available_models(
    region: str = "us-east-1",
    min_context_length: int = 0,
    supports_vision: bool = False,
    supports_function_calling: bool = False,
) -> List[ModelConfig]:
    """Get list of available models matching criteria."""
    models = []
    
    for config in BEDROCK_MODELS.values():
        # Check region
        if region not in config.regions:
            continue
        
        # Check context length
        if config.max_context_length < min_context_length:
            continue
        
        # Check capabilities
        if supports_vision and not config.supports_vision:
            continue
        
        if supports_function_calling and not config.supports_function_calling:
            continue
        
        models.append(config)
    
    return models


def get_cheapest_model(
    models: List[ModelConfig] = None,
    estimated_input_tokens: int = 1000,
    estimated_output_tokens: int = 1000,
) -> ModelConfig:
    """Get the cheapest model from a list."""
    if models is None:
        models = list(BEDROCK_MODELS.values())
    
    if not models:
        raise ValueError("No models available")
    
    # Calculate cost for each model
    model_costs = []
    for model in models:
        if not model.pricing:
            continue
        
        cost = (
            (estimated_input_tokens / 1000) * model.pricing.input_per_1k +
            (estimated_output_tokens / 1000) * model.pricing.output_per_1k
        )
        
        model_costs.append((model, cost))
    
    if not model_costs:
        raise ValueError("No models with pricing information")
    
    # Sort by cost and return cheapest
    model_costs.sort(key=lambda x: x[1])
    return model_costs[0][0]
