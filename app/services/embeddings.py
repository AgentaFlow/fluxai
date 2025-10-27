"""Embedding service for semantic similarity."""

from typing import List, Optional
import json
import hashlib
import structlog
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = structlog.get_logger()


class EmbeddingService:
    """Service for generating embeddings using AWS Bedrock Titan Embeddings."""
    
    def __init__(self):
        """Initialize embedding service."""
        self.model_id = settings.EMBEDDING_MODEL
        self.dimension = settings.EMBEDDING_DIMENSION
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        
        # Initialize Bedrock client
        config = Config(
            region_name=settings.AWS_REGION,
            retries={"max_attempts": 3, "mode": "adaptive"},
        )
        
        self.client = boto3.client(
            service_name="bedrock-runtime",
            config=config,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID or None,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY or None,
        )
        
        logger.info(
            "Embedding service initialized",
            model=self.model_id,
            dimension=self.dimension,
        )
    
    def _generate_embedding_cache_key(self, text: str) -> str:
        """Generate cache key for embedding."""
        hash_value = hashlib.sha256(text.encode()).hexdigest()
        return f"embedding:{self.model_id}:{hash_value[:16]}"
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text to embed
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            ClientError: If Bedrock API call fails
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding")
            return [0.0] * self.dimension
        
        try:
            # Prepare request body for Titan Embeddings
            request_body = {
                "inputText": text.strip(),
            }
            
            # Call Bedrock
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=json.dumps(request_body),
            )
            
            # Parse response
            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding", [])
            
            if not embedding:
                logger.error("Empty embedding returned", text_length=len(text))
                return [0.0] * self.dimension
            
            logger.debug(
                "Generated embedding",
                text_length=len(text),
                embedding_dimension=len(embedding),
            )
            
            return embedding
            
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get("Message", str(e))
            
            logger.error(
                "Failed to generate embedding",
                error_code=error_code,
                error_message=error_message,
                text_length=len(text),
            )
            raise
        except Exception as e:
            logger.error("Unexpected error generating embedding", error=str(e))
            raise
    
    def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Note: Bedrock Titan Embeddings doesn't support true batch processing,
        so this sequentially calls the API for each text.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors in the same order as input texts
        """
        if not texts:
            return []
        
        embeddings = []
        
        for text in texts:
            try:
                embedding = self.generate_embedding(text)
                embeddings.append(embedding)
            except Exception as e:
                logger.error("Failed to embed text in batch", error=str(e))
                # Return zero vector on error
                embeddings.append([0.0] * self.dimension)
        
        logger.info(
            "Generated batch embeddings",
            count=len(texts),
            successful=len([e for e in embeddings if sum(e) != 0]),
        )
        
        return embeddings
    
    def estimate_cost(self, text_length: int) -> float:
        """
        Estimate cost for generating embedding.
        
        Titan Embeddings pricing (as of Jan 2025):
        - $0.0001 per 1K input tokens
        
        Args:
            text_length: Length of input text in characters
            
        Returns:
            Estimated cost in USD
        """
        # Rough estimate: 1 token ≈ 4 characters
        estimated_tokens = text_length / 4
        cost = (estimated_tokens / 1000) * 0.0001
        
        return cost
    
    def get_model_info(self) -> dict:
        """Get information about the embedding model."""
        return {
            "model_id": self.model_id,
            "dimension": self.dimension,
            "batch_size": self.batch_size,
            "provider": "AWS Bedrock",
            "model_name": "Titan Text Embeddings",
        }


# Singleton instance
embedding_service = EmbeddingService()
