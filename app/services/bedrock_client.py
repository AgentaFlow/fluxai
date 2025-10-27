"""AWS Bedrock client service."""

import json
from typing import List, Dict, Any, Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import structlog

from app.core.config import settings
from app.models.schemas import Message, InvokeRequest

logger = structlog.get_logger()


class BedrockService:
    """AWS Bedrock client service."""
    
    def __init__(self):
        """Initialize Bedrock client."""
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize boto3 Bedrock Runtime client."""
        config = Config(
            region_name=settings.AWS_REGION,
            retries={
                'max_attempts': 3,
                'mode': 'adaptive',
            },
        )
        
        self.client = boto3.client(
            'bedrock-runtime',
            config=config,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
        
        logger.info("Bedrock client initialized", region=settings.AWS_REGION)
    
    async def select_model(
        self,
        request: InvokeRequest,
        strategy: str = "cost-optimized",
        max_cost: Optional[float] = None,
    ) -> str:
        """
        Select optimal model based on routing strategy.
        
        For MVP, we'll default to Claude 3.5 Sonnet.
        TODO: Implement intelligent routing strategies.
        """
        if request.model != "auto":
            return request.model
        
        # Default to Claude 3.5 Sonnet for MVP
        default_model = "anthropic.claude-3-5-sonnet-20241022-v2:0"
        
        logger.info(
            "Model selection",
            strategy=strategy,
            selected_model=default_model,
        )
        
        return default_model
    
    def _build_claude_request(
        self,
        messages: List[Message],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Build request body for Claude models."""
        return json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
        })
    
    def _build_llama_request(
        self,
        messages: List[Message],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Build request body for Llama models."""
        # Llama uses a different format
        prompt = "\n".join([
            f"{msg.role}: {msg.content}"
            for msg in messages
        ])
        
        return json.dumps({
            "prompt": prompt,
            "max_gen_len": max_tokens,
            "temperature": temperature,
        })
    
    def _build_request_body(
        self,
        model_id: str,
        messages: List[Message],
        max_tokens: int,
        temperature: float,
    ) -> str:
        """Build request body based on model type."""
        if "anthropic.claude" in model_id:
            return self._build_claude_request(messages, max_tokens, temperature)
        elif "meta.llama" in model_id:
            return self._build_llama_request(messages, max_tokens, temperature)
        else:
            # Default to Claude format
            return self._build_claude_request(messages, max_tokens, temperature)
    
    def _parse_claude_response(self, response_body: Dict) -> Dict[str, Any]:
        """Parse Claude response."""
        content = response_body.get("content", [{}])[0].get("text", "")
        usage = response_body.get("usage", {})
        
        return {
            "content": content,
            "usage": {
                "input_tokens": usage.get("input_tokens", 0),
                "output_tokens": usage.get("output_tokens", 0),
                "total_tokens": usage.get("input_tokens", 0) + usage.get("output_tokens", 0),
            },
        }
    
    def _parse_response(self, model_id: str, response_body: str) -> Dict[str, Any]:
        """Parse response based on model type."""
        body = json.loads(response_body)
        
        if "anthropic.claude" in model_id:
            return self._parse_claude_response(body)
        else:
            # Default to Claude format
            return self._parse_claude_response(body)
    
    async def invoke(
        self,
        model_id: str,
        messages: List[Message],
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Invoke a Bedrock model.
        
        Returns:
            Dict with keys: model_id, content, usage
        """
        try:
            # Build request body
            body = self._build_request_body(
                model_id=model_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            
            logger.info(
                "Invoking Bedrock model",
                model_id=model_id,
                max_tokens=max_tokens,
            )
            
            # Invoke model
            response = self.client.invoke_model(
                modelId=model_id,
                contentType="application/json",
                accept="application/json",
                body=body,
            )
            
            # Parse response
            response_body = response.get("body").read()
            parsed_response = self._parse_response(model_id, response_body)
            
            # Add model_id to response
            parsed_response["model_id"] = model_id
            
            logger.info(
                "Bedrock invocation successful",
                model_id=model_id,
                input_tokens=parsed_response["usage"]["input_tokens"],
                output_tokens=parsed_response["usage"]["output_tokens"],
            )
            
            return parsed_response
            
        except ClientError as e:
            logger.error(
                "Bedrock invocation failed",
                model_id=model_id,
                error=str(e),
                exc_info=True,
            )
            raise Exception(f"Bedrock API error: {str(e)}")
        except Exception as e:
            logger.error(
                "Unexpected error during Bedrock invocation",
                model_id=model_id,
                error=str(e),
                exc_info=True,
            )
            raise


# Singleton instance
bedrock_service = BedrockService()
