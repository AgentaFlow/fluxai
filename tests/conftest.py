"""
Test configuration and fixtures for pytest.
"""

import pytest
from typing import Generator


@pytest.fixture
def sample_invoke_request():
    """Sample Bedrock invoke request for testing."""
    return {
        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
        "messages": [
            {
                "role": "user",
                "content": "What is the capital of France?"
            }
        ],
        "max_tokens": 100,
        "temperature": 0.7,
    }


@pytest.fixture
def sample_bedrock_response():
    """Sample Bedrock API response for testing."""
    return {
        "model_id": "anthropic.claude-3-sonnet-20240229-v1:0",
        "content": "The capital of France is Paris.",
        "usage": {
            "input_tokens": 15,
            "output_tokens": 8,
        },
        "stop_reason": "end_turn",
    }


# Add more fixtures as needed for testing different components
