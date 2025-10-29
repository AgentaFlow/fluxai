# FluxAI Tests

This directory contains the test suite for FluxAI Gateway.

## Structure

```
tests/
├── __init__.py              # Package initialization
├── conftest.py              # Pytest fixtures and configuration
├── test_sanity.py          # Basic sanity tests for CI/CD
├── test_cache.py           # TODO: Semantic cache tests
├── test_cost_calculator.py # TODO: Cost calculator tests
├── test_bedrock.py         # TODO: Bedrock client tests
├── test_api/               # TODO: API endpoint tests
└── test_middleware/        # TODO: Middleware tests
```

## Running Tests

### Locally

```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
pytest tests/test_sanity.py -v

# Run specific test
pytest tests/test_sanity.py::test_sample_fixture -v
```

### With Docker Services

```bash
# Start required services
docker-compose up -d postgres redis

# Run tests
pytest tests/ -v

# Stop services
docker-compose down
```

## CI/CD

Tests run automatically on:
- Push to `main` or `develop` branches
- Pull requests
- Manual workflow trigger

See `.github/workflows/tests.yml` for configuration.

## Test Coverage

Current coverage reports are uploaded to Codecov on CI runs.

View coverage locally:
```bash
pytest tests/ --cov=app --cov-report=html
open htmlcov/index.html
```

## Writing Tests

### Example Test

```python
import pytest
from app.services.cost_calculator import cost_calculator

def test_cost_calculation():
    """Test cost calculation for Claude 3 Sonnet."""
    cost = cost_calculator.calculate(
        model_id="anthropic.claude-3-sonnet-20240229-v1:0",
        input_tokens=100,
        output_tokens=50,
    )
    assert cost.total_cost > 0
    assert cost.input_cost > 0
    assert cost.output_cost > 0
```

### Async Tests

```python
@pytest.mark.asyncio
async def test_cache_service():
    """Test cache service operations."""
    from app.services.cache import cache_service
    
    await cache_service.set(
        prompt="test",
        model_id="test-model",
        response={"content": "test response"},
    )
    
    cached = await cache_service.get(
        prompt="test",
        model_id="test-model",
    )
    
    assert cached is not None
```

## Fixtures

Common fixtures are defined in `conftest.py`:
- `sample_invoke_request` - Example Bedrock request
- `sample_bedrock_response` - Example Bedrock response

## TODO

- [ ] Add cache service tests
- [ ] Add cost calculator tests
- [ ] Add Bedrock client tests
- [ ] Add API endpoint tests
- [ ] Add middleware tests
- [ ] Add database model tests
- [ ] Add integration tests
- [ ] Increase code coverage to 80%+
