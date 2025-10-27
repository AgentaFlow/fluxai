"""
Cost Calculator Service

Real-time cost tracking and calculation for AWS Bedrock requests.
"""

from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import structlog
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.pricing import get_model_pricing, BEDROCK_PRICING

logger = structlog.get_logger()


@dataclass
class CostBreakdown:
    """Detailed cost breakdown for a request."""
    
    input_cost: float
    output_cost: float
    total_cost: float
    model_id: str
    input_tokens: int
    output_tokens: int
    region: str
    timestamp: str = None
    
    def __post_init__(self):
        """Set timestamp after initialization if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class CostSavings:
    """Cost savings from cache hits."""
    
    requests_saved: int
    cost_saved: float
    tokens_saved: int
    embedding_cost: float = 0.0
    net_savings: float = 0.0
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class DailyCostSummary:
    """Daily cost summary for an account."""
    
    date: str
    total_cost: float
    total_requests: int
    total_input_tokens: int
    total_output_tokens: int
    total_tokens: int
    cache_hits: int
    cache_savings: float
    breakdown_by_model: Dict[str, Dict]
    breakdown_by_region: Dict[str, float]


@dataclass
class CostForecast:
    """Cost forecast for future periods."""
    
    estimated_monthly_cost: float
    estimated_daily_cost: float
    confidence: float
    potential_savings: float
    recommendations: List[str]
    forecast_date: str = None
    
    def __post_init__(self):
        """Set forecast_date after initialization if not provided."""
        if self.forecast_date is None:
            self.forecast_date = datetime.now().isoformat()


class CostCalculator:
    """
    Real-time cost calculator for Bedrock requests.
    
    Features:
    - Accurate per-request cost calculation
    - Cache savings tracking
    - Cost forecasting
    - Multi-model cost comparison
    - Regional pricing support
    """
    
    def __init__(self):
        self.pricing_cache = BEDROCK_PRICING.copy()
        logger.info(
            "Cost calculator initialized",
            models_loaded=len(self.pricing_cache),
        )
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimate number of tokens in text.
        
        Uses rough approximation: 1 token ≈ 4 characters.
        For production, consider using tiktoken or similar.
        
        Args:
            text: Input text
            
        Returns:
            Estimated token count
        """
        return max(1, len(text) // 4)
    
    def calculate(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        region: str = "us-east-1",
    ) -> Dict[str, float]:
        """
        Calculate cost for a request (legacy method for backward compatibility).
        
        Returns:
            Dict with keys: input, output, total
        """
        breakdown = self.calculate_cost(model_id, input_tokens, output_tokens, region)
        return {
            "input": breakdown.input_cost,
            "output": breakdown.output_cost,
            "total": breakdown.total_cost,
        }
    
    def calculate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        region: str = "us-east-1",
    ) -> CostBreakdown:
        """
        Calculate cost for a specific request.
        
        Args:
            model_id: Bedrock model ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            region: AWS region
            
        Returns:
            CostBreakdown object with detailed cost information
        """
        pricing = get_model_pricing(model_id, region)
        
        if not pricing:
            logger.warning(
                "No pricing found for model, using default",
                model_id=model_id,
                region=region,
            )
            # Default to Claude 3.5 Sonnet pricing as fallback
            pricing = get_model_pricing(
                "anthropic.claude-3-5-sonnet-20241022-v2:0",
                region,
            )
        
        # Calculate costs
        input_cost = (input_tokens / 1000.0) * pricing.input_per_1k
        output_cost = (output_tokens / 1000.0) * pricing.output_per_1k
        total_cost = input_cost + output_cost
        
        logger.debug(
            "Cost calculated",
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_cost=total_cost,
        )
        
        return CostBreakdown(
            input_cost=round(input_cost, 6),
            output_cost=round(output_cost, 6),
            total_cost=round(total_cost, 6),
            model_id=model_id,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            region=region,
        )
    
    def estimate_cost(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        region: str = "us-east-1",
    ) -> float:
        """
        Estimate total cost for a request (used by router).
        
        Args:
            model_id: Bedrock model ID
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            region: AWS region
            
        Returns:
            Estimated total cost
        """
        breakdown = self.calculate_cost(model_id, input_tokens, output_tokens, region)
        return breakdown.total_cost
    
    def calculate_cache_savings(
        self,
        model_id: str,
        input_tokens: int,
        output_tokens: int,
        region: str = "us-east-1",
        include_embedding_cost: bool = True,
    ) -> CostSavings:
        """
        Calculate savings from a cache hit.
        
        Args:
            model_id: Model that would have been used
            input_tokens: Tokens that would have been sent
            output_tokens: Tokens that would have been generated
            region: AWS region
            include_embedding_cost: Whether to subtract embedding cost
            
        Returns:
            CostSavings object
        """
        # Cost that would have been incurred
        bedrock_cost = self.calculate_cost(
            model_id, input_tokens, output_tokens, region
        )
        
        # Cost of generating embedding (if applicable)
        embedding_cost = 0.0
        if include_embedding_cost:
            embedding_pricing = get_model_pricing(
                "amazon.titan-embed-text-v1",
                region,
            )
            if embedding_pricing:
                embedding_cost = (input_tokens / 1000.0) * embedding_pricing.input_per_1k
        
        # Net savings
        net_savings = bedrock_cost.total_cost - embedding_cost
        
        return CostSavings(
            requests_saved=1,
            cost_saved=bedrock_cost.total_cost,
            tokens_saved=input_tokens + output_tokens,
            embedding_cost=round(embedding_cost, 6),
            net_savings=round(net_savings, 6),
        )
    
    def compare_model_costs(
        self,
        model_ids: List[str],
        input_tokens: int,
        output_tokens: int,
        region: str = "us-east-1",
    ) -> Dict[str, CostBreakdown]:
        """
        Compare costs across multiple models.
        
        Args:
            model_ids: List of model IDs to compare
            input_tokens: Input token count
            output_tokens: Output token count
            region: AWS region
            
        Returns:
            Dictionary mapping model_id to CostBreakdown
        """
        comparisons = {}
        for model_id in model_ids:
            try:
                cost = self.calculate_cost(
                    model_id, input_tokens, output_tokens, region
                )
                comparisons[model_id] = cost
            except Exception as e:
                logger.warning(
                    "Failed to calculate cost for model",
                    model_id=model_id,
                    error=str(e),
                )
        
        return comparisons
    
    def get_cheapest_model(
        self,
        input_tokens: int,
        output_tokens: int,
        model_ids: Optional[List[str]] = None,
        region: str = "us-east-1",
    ) -> tuple[str, CostBreakdown]:
        """
        Find the cheapest model for given token counts.
        
        Args:
            input_tokens: Input token count
            output_tokens: Output token count
            model_ids: Optional list of models to consider
            region: AWS region
            
        Returns:
            Tuple of (model_id, CostBreakdown)
        """
        if model_ids is None:
            model_ids = list(self.pricing_cache.keys())
            # Exclude embedding model from comparison
            model_ids = [m for m in model_ids if "embed" not in m]
        
        comparisons = self.compare_model_costs(
            model_ids, input_tokens, output_tokens, region
        )
        
        if not comparisons:
            raise ValueError("No valid models for cost comparison")
        
        # Find cheapest
        cheapest = min(
            comparisons.items(),
            key=lambda x: x[1].total_cost
        )
        
        logger.info(
            "Cheapest model identified",
            model_id=cheapest[0],
            cost=cheapest[1].total_cost,
            alternatives=len(comparisons),
        )
        
        return cheapest
    
    def get_pricing(self, model_id: str) -> Dict[str, float]:
        """
        Get pricing for a specific model (legacy method).
        
        Returns:
            Dict with keys: input_per_1k, output_per_1k
        """
        pricing = get_model_pricing(model_id)
        if pricing:
            return {
                "input_per_1k": pricing.input_per_1k,
                "output_per_1k": pricing.output_per_1k,
            }
        return {
            "input_per_1k": 0.003,
            "output_per_1k": 0.015,
        }
    
    def calculate_optimization_potential(
        self,
        total_requests: int,
        current_cache_hit_rate: float,
        avg_cost_per_request: float,
        target_cache_hit_rate: float = 0.50,
    ) -> Dict[str, float]:
        """
        Calculate potential savings from optimization.
        
        Args:
            total_requests: Total number of requests
            current_cache_hit_rate: Current cache hit rate (0-1)
            avg_cost_per_request: Average cost per request
            target_cache_hit_rate: Target cache hit rate (0-1)
            
        Returns:
            Dictionary with savings estimates
        """
        current_cost = total_requests * avg_cost_per_request
        
        # Calculate savings with improved cache hit rate
        improvement = target_cache_hit_rate - current_cache_hit_rate
        potential_cache_savings = (
            total_requests * improvement * avg_cost_per_request
        )
        
        # Calculate savings from routing optimization
        # Based on studies showing 10-20% cost reduction from optimal model selection
        # Conservative estimate of 15% assumes mix of simple/complex queries
        ROUTING_OPTIMIZATION_FACTOR = 0.15
        potential_routing_savings = current_cost * ROUTING_OPTIMIZATION_FACTOR
        potential_routing_savings = current_cost * 0.15
        
        total_potential_savings = (
            potential_cache_savings + potential_routing_savings
        )
        
        return {
            "current_monthly_cost": round(current_cost, 2),
            "potential_cache_savings": round(potential_cache_savings, 2),
            "potential_routing_savings": round(potential_routing_savings, 2),
            "total_potential_savings": round(total_potential_savings, 2),
            "potential_monthly_cost": round(
                current_cost - total_potential_savings, 2
            ),
            "savings_percentage": round(
                (total_potential_savings / current_cost) * 100, 1
            ),
        }


# Singleton instance
cost_calculator = CostCalculator()
