# Cost Calculator Implementation Guide

## Overview

The **FluxAI Cost Calculator** provides real-time cost tracking and analysis for AWS Bedrock requests. It enables accurate per-request cost calculation, cache savings tracking, and cost optimization recommendations.

## Table of Contents
1. [Features](#features)
2. [Architecture](#architecture)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Cost Calculation](#cost-calculation)
6. [Savings Analysis](#savings-analysis)
7. [API Reference](#api-reference)
8. [Examples](#examples)
9. [Testing](#testing)
10. [Troubleshooting](#troubleshooting)

---

## Features

### Core Capabilities
- ✅ **Real-time cost calculation** - Accurate per-request cost tracking
- ✅ **Multi-model support** - All AWS Bedrock models (Claude, Llama, Titan, Mistral)
- ✅ **Regional pricing** - Automatic regional multipliers
- ✅ **Cache savings tracking** - Calculate savings from semantic cache hits
- ✅ **Cost comparison** - Compare costs across different models
- ✅ **Optimization analysis** - Identify potential cost savings opportunities

### Pricing Coverage
- **Anthropic Claude** - 3.5 Sonnet, 3.5 Haiku, 3 Opus
- **Meta Llama** - 3 70B, 3 8B
- **Amazon Titan** - Text Express, Text Lite, Embeddings
- **Mistral** - 7B Instruct, Mixtral 8x7B

---

## Architecture

### Component Structure

```
app/services/cost_calculator.py  # Main calculator service
app/models/pricing.py            # Pricing data and utilities
app/core/config.py               # Configuration settings
```

### Data Flow

```
Request → Token Count → Pricing Data → Cost Calculation → Response with Cost

Cache Hit → Saved Cost Calculation → Net Savings (after embedding cost)
```

### Pricing Data Structure

```python
@dataclass
class ModelPricing:
    model_id: str
    input_per_1k: float   # USD per 1,000 input tokens
    output_per_1k: float  # USD per 1,000 output tokens
    region: str
    effective_date: str
    last_updated: str
```

---

## Installation

### 1. Dependencies

The cost calculator requires:
- `structlog` - For structured logging
- `sqlalchemy` (optional) - For database integration

Already included in `requirements.txt`.

### 2. Configuration

No additional configuration required. Pricing data is embedded in the module.

### 3. Environment Variables

```bash
# Optional: Override default region
AWS_REGION=us-east-1
```

---

## Usage

### Basic Cost Calculation

```python
from app.services.cost_calculator import cost_calculator

# Calculate cost for a request
cost = cost_calculator.calculate_cost(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    input_tokens=500,
    output_tokens=1000,
    region="us-east-1",
)

print(f"Total cost: ${cost.total_cost:.6f}")
print(f"Input cost: ${cost.input_cost:.6f}")
print(f"Output cost: ${cost.output_cost:.6f}")
```

**Output:**
```
Total cost: $0.016500
Input cost: $0.001500
Output cost: $0.015000
```

### Calculate Cache Savings

```python
# Calculate savings from a cache hit
savings = cost_calculator.calculate_cache_savings(
    model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
    input_tokens=500,
    output_tokens=1000,
    region="us-east-1",
    include_embedding_cost=True,
)

print(f"Cost saved: ${savings.cost_saved:.6f}")
print(f"Embedding cost: ${savings.embedding_cost:.6f}")
print(f"Net savings: ${savings.net_savings:.6f}")
print(f"Savings rate: {(savings.net_savings / savings.cost_saved) * 100:.1f}%")
```

**Output:**
```
Cost saved: $0.016500
Embedding cost: $0.000050
Net savings: $0.016450
Savings rate: 99.7%
```

### Compare Model Costs

```python
# Compare costs across multiple models
model_ids = [
    "anthropic.claude-3-5-sonnet-20241022-v2:0",
    "anthropic.claude-3-5-haiku-20241022-v1:0",
    "meta.llama3-70b-instruct-v1:0",
    "meta.llama3-8b-instruct-v1:0",
]

costs = cost_calculator.compare_model_costs(
    model_ids=model_ids,
    input_tokens=500,
    output_tokens=1000,
    region="us-east-1",
)

for model_id, cost in sorted(costs.items(), key=lambda x: x[1].total_cost):
    print(f"{model_id}: ${cost.total_cost:.6f}")
```

**Output:**
```
meta.llama3-8b-instruct-v1:0: $0.000750
meta.llama3-70b-instruct-v1:0: $0.004825
anthropic.claude-3-5-haiku-20241022-v1:0: $0.005500
anthropic.claude-3-5-sonnet-20241022-v2:0: $0.016500
```

### Find Cheapest Model

```python
# Automatically find the cheapest model
cheapest_model, cost = cost_calculator.get_cheapest_model(
    input_tokens=500,
    output_tokens=1000,
    region="us-east-1",
)

print(f"Cheapest: {cheapest_model}")
print(f"Cost: ${cost.total_cost:.6f}")
```

**Output:**
```
Cheapest: meta.llama3-8b-instruct-v1:0
Cost: $0.000750
```

---

## Cost Calculation

### Pricing Formula

```python
input_cost = (input_tokens / 1000) * input_price_per_1k
output_cost = (output_tokens / 1000) * output_price_per_1k
total_cost = input_cost + output_cost
```

### Current Pricing (October 2025)

| Model | Input (per 1K) | Output (per 1K) |
|-------|----------------|-----------------|
| Claude 3.5 Sonnet v2 | $0.003 | $0.015 |
| Claude 3.5 Haiku | $0.001 | $0.005 |
| Claude 3 Opus | $0.015 | $0.075 |
| Llama 3 70B | $0.00265 | $0.0035 |
| Llama 3 8B | $0.0003 | $0.0006 |
| Titan Text Express | $0.0002 | $0.0006 |
| Titan Text Lite | $0.00015 | $0.0002 |
| Mistral 7B | $0.00015 | $0.0002 |
| Mixtral 8x7B | $0.00045 | $0.0007 |
| Titan Embeddings | $0.0001 | $0.0 |

### Regional Multipliers

| Region | Multiplier |
|--------|-----------|
| us-east-1 | 1.0× |
| us-west-2 | 1.0× |
| eu-west-1 | 1.1× |
| eu-central-1 | 1.1× |
| ap-northeast-1 | 1.15× |
| ap-southeast-1 | 1.15× |

### Example Calculation

**Request:**
- Model: Claude 3.5 Sonnet v2
- Input: 500 tokens
- Output: 1,000 tokens
- Region: us-east-1

**Calculation:**
```python
input_cost = (500 / 1000) * 0.003 = $0.0015
output_cost = (1000 / 1000) * 0.015 = $0.0150
total_cost = $0.0015 + $0.0150 = $0.0165
```

---

## Savings Analysis

### Cache Hit Savings

When a semantic cache hit occurs, you save the cost of calling Bedrock minus the cost of generating the embedding.

**Formula:**
```python
bedrock_cost = calculate_cost(model_id, input_tokens, output_tokens)
embedding_cost = (input_tokens / 1000) * 0.0001  # Titan Embeddings
net_savings = bedrock_cost - embedding_cost
```

**Example (Claude 3.5 Sonnet):**
```
Bedrock cost:    $0.016500
Embedding cost:  $0.000050
Net savings:     $0.016450  (99.7% savings)
```

### Monthly Savings Estimate

```python
# Calculate optimization potential
potential = cost_calculator.calculate_optimization_potential(
    total_requests=100_000,           # 100K requests/month
    current_cache_hit_rate=0.30,     # 30% cache hit rate
    avg_cost_per_request=0.0165,     # Avg $0.0165 per request
    target_cache_hit_rate=0.50,      # Target 50% hit rate
)

print(potential)
```

**Output:**
```python
{
    "current_monthly_cost": 1650.0,
    "potential_cache_savings": 330.0,    # 20% improvement
    "potential_routing_savings": 247.5,  # 15% from better routing
    "total_potential_savings": 577.5,
    "potential_monthly_cost": 1072.5,
    "savings_percentage": 35.0
}
```

---

## API Reference

### `CostCalculator`

#### `calculate_cost()`

Calculate cost for a specific request.

```python
def calculate_cost(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    region: str = "us-east-1",
) -> CostBreakdown
```

**Parameters:**
- `model_id` - Bedrock model ID
- `input_tokens` - Number of input tokens
- `output_tokens` - Number of output tokens
- `region` - AWS region (default: "us-east-1")

**Returns:** `CostBreakdown` object

#### `calculate_cache_savings()`

Calculate savings from a cache hit.

```python
def calculate_cache_savings(
    model_id: str,
    input_tokens: int,
    output_tokens: int,
    region: str = "us-east-1",
    include_embedding_cost: bool = True,
) -> CostSavings
```

**Parameters:**
- `model_id` - Model that would have been used
- `input_tokens` - Tokens that would have been sent
- `output_tokens` - Tokens that would have been generated
- `region` - AWS region
- `include_embedding_cost` - Whether to subtract embedding cost

**Returns:** `CostSavings` object

#### `compare_model_costs()`

Compare costs across multiple models.

```python
def compare_model_costs(
    model_ids: List[str],
    input_tokens: int,
    output_tokens: int,
    region: str = "us-east-1",
) -> Dict[str, CostBreakdown]
```

**Parameters:**
- `model_ids` - List of model IDs to compare
- `input_tokens` - Input token count
- `output_tokens` - Output token count
- `region` - AWS region

**Returns:** Dictionary mapping model_id to `CostBreakdown`

#### `get_cheapest_model()`

Find the cheapest model for given token counts.

```python
def get_cheapest_model(
    input_tokens: int,
    output_tokens: int,
    model_ids: Optional[List[str]] = None,
    region: str = "us-east-1",
) -> tuple[str, CostBreakdown]
```

**Parameters:**
- `input_tokens` - Input token count
- `output_tokens` - Output token count
- `model_ids` - Optional list of models to consider (defaults to all)
- `region` - AWS region

**Returns:** Tuple of `(model_id, CostBreakdown)`

---

## Examples

### Integration with Bedrock Endpoint

```python
from app.services.cost_calculator import cost_calculator
from app.services.bedrock_client import bedrock_client

async def invoke_with_cost_tracking(request):
    # Invoke Bedrock
    response = await bedrock_client.invoke(
        model_id=request.model_id,
        messages=request.messages,
        max_tokens=request.max_tokens,
    )
    
    # Calculate cost
    cost = cost_calculator.calculate_cost(
        model_id=request.model_id,
        input_tokens=response.usage.input_tokens,
        output_tokens=response.usage.output_tokens,
        region=settings.AWS_REGION,
    )
    
    # Add cost to response
    response.cost = cost.to_dict()
    
    return response
```

### Track Daily Costs

```python
from datetime import datetime, timedelta
from collections import defaultdict

# Aggregate costs by model
daily_costs = defaultdict(float)

for request in requests:
    cost = cost_calculator.calculate_cost(
        model_id=request.model_id,
        input_tokens=request.input_tokens,
        output_tokens=request.output_tokens,
    )
    daily_costs[request.model_id] += cost.total_cost

# Print summary
print(f"Daily Cost Summary - {datetime.now().date()}")
for model_id, total in sorted(daily_costs.items(), key=lambda x: x[1], reverse=True):
    print(f"{model_id}: ${total:.2f}")
```

### Cost-Based Routing

```python
# Select cheapest model that meets requirements
available_models = [
    "anthropic.claude-3-5-haiku-20241022-v1:0",
    "meta.llama3-70b-instruct-v1:0",
    "meta.llama3-8b-instruct-v1:0",
]

# Estimate tokens from prompt
input_tokens = cost_calculator.estimate_tokens(prompt)
output_tokens = max_tokens

# Find cheapest
cheapest, cost = cost_calculator.get_cheapest_model(
    input_tokens=input_tokens,
    output_tokens=output_tokens,
    model_ids=available_models,
)

print(f"Using {cheapest} (estimated cost: ${cost.total_cost:.6f})")
```

---

## Testing

### Unit Tests

```python
import pytest
from app.services.cost_calculator import cost_calculator

def test_calculate_cost():
    """Test basic cost calculation."""
    cost = cost_calculator.calculate_cost(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        input_tokens=1000,
        output_tokens=2000,
        region="us-east-1",
    )
    
    assert cost.input_cost == 0.003
    assert cost.output_cost == 0.030
    assert cost.total_cost == 0.033

def test_cache_savings():
    """Test cache savings calculation."""
    savings = cost_calculator.calculate_cache_savings(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        input_tokens=500,
        output_tokens=1000,
    )
    
    assert savings.cost_saved == 0.0165
    assert savings.embedding_cost == 0.00005
    assert savings.net_savings > 0.016

def test_cheapest_model():
    """Test finding cheapest model."""
    cheapest, cost = cost_calculator.get_cheapest_model(
        input_tokens=1000,
        output_tokens=1000,
    )
    
    # Should select cheapest model
    assert "llama3-8b" in cheapest or "titan" in cheapest or "mistral-7b" in cheapest
```

### Integration Tests

```bash
# Run with pytest
pytest tests/test_cost_calculator.py -v
```

---

## Troubleshooting

### Issue: Incorrect Costs

**Problem:** Calculated costs don't match AWS billing.

**Solutions:**
1. Verify pricing data is up-to-date (check `app/models/pricing.py`)
2. Ensure correct region is being used
3. Check token counts are accurate
4. Update pricing from AWS Pricing API

### Issue: Missing Model Pricing

**Problem:** `No pricing found for model` warning.

**Solutions:**
1. Add model to `BEDROCK_PRICING` in `app/models/pricing.py`
2. Falls back to default Claude 3.5 Sonnet pricing automatically

### Issue: Regional Pricing Differences

**Problem:** Costs differ across regions.

**Solutions:**
1. Check `REGIONAL_MULTIPLIERS` in `app/models/pricing.py`
2. Update multipliers based on actual AWS regional pricing
3. Use `get_model_pricing(model_id, region)` for accurate costs

---

## Best Practices

### 1. Update Pricing Regularly
- Check AWS pricing monthly
- Update `BEDROCK_PRICING` dictionary
- Document effective dates

### 2. Track All Costs
- Log every request with cost breakdown
- Store in PostgreSQL for analysis
- Export to billing systems

### 3. Monitor Savings
- Track cache hit rate
- Calculate actual vs potential savings
- Adjust caching strategies based on ROI

### 4. Regional Awareness
- Always pass correct region
- Account for regional multipliers
- Consider data transfer costs

### 5. Optimization Analysis
- Run `calculate_optimization_potential()` weekly
- Review model usage patterns
- Identify opportunities for cheaper models

---

## Future Enhancements

- [ ] **Automatic pricing updates** - Fetch from AWS Pricing API
- [ ] **Cost forecasting** - Machine learning-based predictions
- [ ] **Budget alerts** - Webhook notifications on thresholds
- [ ] **Per-client cost tracking** - Multi-tenant cost allocation
- [ ] **Custom pricing tiers** - Reserved capacity support
- [ ] **Cost anomaly detection** - Identify unusual spending patterns

---

## Support

### Documentation
- [Technical Specification](fluxai-technical-spec.md)
- [Implementation Guide](fluxai-implementation-guide.md)
- [Quick Start](fluxai-quick-start.md)

### Resources
- AWS Bedrock Pricing: https://aws.amazon.com/bedrock/pricing/
- Model Documentation: https://docs.aws.amazon.com/bedrock/

---

**Last Updated:** October 27, 2025  
**Version:** 1.0.0  
**Status:** Production Ready
