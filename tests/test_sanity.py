"""
Basic sanity tests to verify test infrastructure is working.

These tests ensure the CI/CD pipeline is functional.
Once real tests are added, these can be removed.
"""

import pytest


def test_import_app():
    """Test that the app package can be imported."""
    try:
        import app
        assert app is not None
    except ImportError:
        pytest.skip("App package not in path - expected in CI environment")


def test_sample_fixture(sample_invoke_request):
    """Test that pytest fixtures are working."""
    assert sample_invoke_request is not None
    assert "model_id" in sample_invoke_request
    assert "messages" in sample_invoke_request


def test_sample_response_fixture(sample_bedrock_response):
    """Test that response fixtures are working."""
    assert sample_bedrock_response is not None
    assert "content" in sample_bedrock_response
    assert "usage" in sample_bedrock_response


@pytest.mark.asyncio
async def test_async_support():
    """Test that async tests are supported."""
    async def async_function():
        return "async works"
    
    result = await async_function()
    assert result == "async works"


class TestBasicMath:
    """Example test class to verify test discovery."""
    
    def test_addition(self):
        """Test basic addition."""
        assert 1 + 1 == 2
    
    def test_subtraction(self):
        """Test basic subtraction."""
        assert 5 - 3 == 2


# TODO: Add real tests for:
# - Semantic cache service
# - Cost calculator
# - Bedrock client
# - API endpoints
# - Middleware
# - Database models
