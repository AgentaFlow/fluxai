"""
AWS Bedrock Model Pricing Data

Current pricing as of October 2025.
Source: https://aws.amazon.com/bedrock/pricing/

Note: Prices may vary by region. Update this file regularly.
"""

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ModelPricing:
    """Pricing information for a Bedrock model."""
    
    model_id: str
    input_per_1k: float  # USD per 1K input tokens
    output_per_1k: float  # USD per 1K output tokens
    region: str = "us-east-1"
    effective_date: str = "2025-10-01"
    last_updated: str = datetime.now().isoformat()


# Current Bedrock pricing (as of October 2025)
BEDROCK_PRICING: Dict[str, ModelPricing] = {
    # Anthropic Claude 3.5 Sonnet v2
    "anthropic.claude-3-5-sonnet-20241022-v2:0": ModelPricing(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        input_per_1k=0.003,
        output_per_1k=0.015,
    ),
    
    # Anthropic Claude 3.5 Haiku
    "anthropic.claude-3-5-haiku-20241022-v1:0": ModelPricing(
        model_id="anthropic.claude-3-5-haiku-20241022-v1:0",
        input_per_1k=0.001,
        output_per_1k=0.005,
    ),
    
    # Anthropic Claude 3 Opus
    "anthropic.claude-3-opus-20240229-v1:0": ModelPricing(
        model_id="anthropic.claude-3-opus-20240229-v1:0",
        input_per_1k=0.015,
        output_per_1k=0.075,
    ),
    
    # Meta Llama 3 70B Instruct
    "meta.llama3-70b-instruct-v1:0": ModelPricing(
        model_id="meta.llama3-70b-instruct-v1:0",
        input_per_1k=0.00265,
        output_per_1k=0.0035,
    ),
    
    # Meta Llama 3 8B Instruct
    "meta.llama3-8b-instruct-v1:0": ModelPricing(
        model_id="meta.llama3-8b-instruct-v1:0",
        input_per_1k=0.0003,
        output_per_1k=0.0006,
    ),
    
    # Amazon Titan Text Express
    "amazon.titan-text-express-v1": ModelPricing(
        model_id="amazon.titan-text-express-v1",
        input_per_1k=0.0002,
        output_per_1k=0.0006,
    ),
    
    # Amazon Titan Text Lite
    "amazon.titan-text-lite-v1": ModelPricing(
        model_id="amazon.titan-text-lite-v1",
        input_per_1k=0.00015,
        output_per_1k=0.0002,
    ),
    
    # Mistral 7B Instruct
    "mistral.mistral-7b-instruct-v0:2": ModelPricing(
        model_id="mistral.mistral-7b-instruct-v0:2",
        input_per_1k=0.00015,
        output_per_1k=0.0002,
    ),
    
    # Mistral Mixtral 8x7B Instruct
    "mistral.mixtral-8x7b-instruct-v0:1": ModelPricing(
        model_id="mistral.mixtral-8x7b-instruct-v0:1",
        input_per_1k=0.00045,
        output_per_1k=0.0007,
    ),
    
    # AWS Bedrock Titan Embeddings (for semantic cache)
    "amazon.titan-embed-text-v1": ModelPricing(
        model_id="amazon.titan-embed-text-v1",
        input_per_1k=0.0001,
        output_per_1k=0.0,  # No output tokens for embeddings
    ),
}


# Regional pricing multipliers (some regions cost more)
REGIONAL_MULTIPLIERS: Dict[str, float] = {
    "us-east-1": 1.0,
    "us-west-2": 1.0,
    "eu-west-1": 1.1,
    "eu-central-1": 1.1,
    "ap-northeast-1": 1.15,
    "ap-southeast-1": 1.15,
}


def get_model_pricing(
    model_id: str,
    region: str = "us-east-1",
) -> Optional[ModelPricing]:
    """
    Get pricing for a specific model and region.
    
    Args:
        model_id: Bedrock model ID
        region: AWS region
        
    Returns:
        ModelPricing object or None if not found
    """
    base_pricing = BEDROCK_PRICING.get(model_id)
    if not base_pricing:
        return None
    
    # Apply regional multiplier
    multiplier = REGIONAL_MULTIPLIERS.get(region, 1.0)
    
    return ModelPricing(
        model_id=model_id,
        input_per_1k=base_pricing.input_per_1k * multiplier,
        output_per_1k=base_pricing.output_per_1k * multiplier,
        region=region,
        effective_date=base_pricing.effective_date,
        last_updated=base_pricing.last_updated,
    )


def get_all_model_pricing(region: str = "us-east-1") -> Dict[str, ModelPricing]:
    """
    Get pricing for all models in a specific region.
    
    Args:
        region: AWS region
        
    Returns:
        Dictionary of model_id -> ModelPricing
    """
    return {
        model_id: get_model_pricing(model_id, region)
        for model_id in BEDROCK_PRICING.keys()
    }


def compare_model_costs(
    model_ids: list[str],
    input_tokens: int,
    output_tokens: int,
    region: str = "us-east-1",
) -> Dict[str, float]:
    """
    Compare costs across multiple models for the same request.
    
    Args:
        model_ids: List of model IDs to compare
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        region: AWS region
        
    Returns:
        Dictionary of model_id -> estimated_cost
    """
    costs = {}
    for model_id in model_ids:
        pricing = get_model_pricing(model_id, region)
        if pricing:
            cost = (
                (input_tokens / 1000) * pricing.input_per_1k +
                (output_tokens / 1000) * pricing.output_per_1k
            )
            costs[model_id] = cost
    
    return costs


def get_cheapest_model(
    input_tokens: int,
    output_tokens: int,
    model_ids: Optional[list[str]] = None,
    region: str = "us-east-1",
) -> tuple[str, float]:
    """
    Find the cheapest model for a given request.
    
    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        model_ids: Optional list of models to consider (defaults to all)
        region: AWS region
        
    Returns:
        Tuple of (model_id, cost)
    """
    if model_ids is None:
        model_ids = list(BEDROCK_PRICING.keys())
    
    costs = compare_model_costs(model_ids, input_tokens, output_tokens, region)
    
    if not costs:
        raise ValueError("No valid models found for cost comparison")
    
    cheapest = min(costs.items(), key=lambda x: x[1])
    return cheapest
