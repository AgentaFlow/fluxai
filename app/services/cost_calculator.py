"""Cost calculator service."""

from typing import Dict
from decimal import Decimal
import structlog

logger = structlog.get_logger()


class CostCalculator:
    """Calculate costs for Bedrock requests."""
    
    def __init__(self):
        """Initialize cost calculator with current pricing."""
        self.pricing = self._load_pricing()
    
    def _load_pricing(self) -> Dict[str, Dict[str, float]]:
        """
        Load current AWS Bedrock pricing.
        
        Pricing as of October 2025 (USD per 1K tokens).
        """
        return {
            "anthropic.claude-3-5-sonnet-20241022-v2:0": {
                "input_per_1k": 0.003,
                "output_per_1k": 0.015,
            },
            "anthropic.claude-3-5-haiku-20241022-v1:0": {
                "input_per_1k": 0.001,
                "output_per_1k": 0.005,
            },
            "anthropic.claude-3-opus-20240229-v1:0": {
                "input_per_1k": 0.015,
                "output_per_1k": 0.075,
            },
            "meta.llama3-70b-instruct-v1:0": {
                "input_per_1k": 0.00195,
                "output_per_1k": 0.00256,
            },
            "meta.llama3-8b-instruct-v1:0": {
                "input_per_1k": 0.0003,
                "output_per_1k": 0.0006,
            },
            "amazon.titan-text-express-v1": {
                "input_per_1k": 0.0002,
                "output_per_1k": 0.0006,
            },
            "mistral.mistral-7b-instruct-v0:2": {
                "input_per_1k": 0.00015,
                "output_per_1k": 0.0002,
            },
            "mistral.mixtral-8x7b-instruct-v0:1": {
                "input_per_1k": 0.00045,
                "output_per_1k": 0.0007,
            },
        }
    
    def calculate(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
    ) -> Dict[str, float]:
        """
        Calculate cost for a request.
        
        Returns:
            Dict with keys: input, output, total
        """
        # Get pricing for model
        pricing = self.pricing.get(model_id)
        
        if not pricing:
            # Default pricing if model not found
            logger.warning(
                "Pricing not found for model, using default",
                model_id=model_id,
            )
            pricing = {
                "input_per_1k": 0.003,
                "output_per_1k": 0.015,
            }
        
        # Calculate costs
        input_cost = (input_tokens / 1000.0) * pricing["input_per_1k"]
        output_cost = (output_tokens / 1000.0) * pricing["output_per_1k"]
        total_cost = input_cost + output_cost
        
        logger.debug(
            "Cost calculated",
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_cost=total_cost,
        )
        
        return {
            "input": round(input_cost, 6),
            "output": round(output_cost, 6),
            "total": round(total_cost, 6),
        }
    
    def get_pricing(self, model_id: str) -> Dict[str, float]:
        """Get pricing for a specific model."""
        return self.pricing.get(model_id, {
            "input_per_1k": 0.003,
            "output_per_1k": 0.015,
        })


# Singleton instance
cost_calculator = CostCalculator()
