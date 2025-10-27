"""Vector similarity utilities for semantic caching."""

from typing import List
import numpy as np


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Cosine similarity score between -1 and 1
        (1 = identical, 0 = orthogonal, -1 = opposite)
    """
    if not vec1 or not vec2:
        return 0.0
    
    if len(vec1) != len(vec2):
        raise ValueError(f"Vector dimensions must match: {len(vec1)} vs {len(vec2)}")
    
    # Convert to numpy arrays for efficient computation
    a = np.array(vec1)
    b = np.array(vec2)
    
    # Calculate cosine similarity
    dot_product = np.dot(a, b)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    similarity = dot_product / (norm_a * norm_b)
    
    # Ensure result is in valid range due to floating point errors
    return float(np.clip(similarity, -1.0, 1.0))


def normalize_vector(vec: List[float]) -> List[float]:
    """
    Normalize a vector to unit length.
    
    Args:
        vec: Input vector
        
    Returns:
        Normalized vector with unit length
    """
    if not vec:
        return []
    
    arr = np.array(vec)
    norm = np.linalg.norm(arr)
    
    if norm == 0:
        return vec
    
    normalized = arr / norm
    return normalized.tolist()


def euclidean_distance(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate Euclidean distance between two vectors.
    
    Args:
        vec1: First vector
        vec2: Second vector
        
    Returns:
        Euclidean distance (lower = more similar)
    """
    if not vec1 or not vec2:
        return float('inf')
    
    if len(vec1) != len(vec2):
        raise ValueError(f"Vector dimensions must match: {len(vec1)} vs {len(vec2)}")
    
    a = np.array(vec1)
    b = np.array(vec2)
    
    return float(np.linalg.norm(a - b))


def batch_cosine_similarity(query_vec: List[float], vectors: List[List[float]]) -> List[float]:
    """
    Calculate cosine similarity between a query vector and multiple vectors.
    
    Args:
        query_vec: Query vector
        vectors: List of vectors to compare against
        
    Returns:
        List of similarity scores in the same order as input vectors
    """
    if not query_vec or not vectors:
        return []
    
    query = np.array(query_vec)
    query_norm = np.linalg.norm(query)
    
    if query_norm == 0:
        return [0.0] * len(vectors)
    
    similarities = []
    for vec in vectors:
        if not vec or len(vec) != len(query_vec):
            similarities.append(0.0)
            continue
        
        v = np.array(vec)
        v_norm = np.linalg.norm(v)
        
        if v_norm == 0:
            similarities.append(0.0)
        else:
            similarity = np.dot(query, v) / (query_norm * v_norm)
            similarities.append(float(np.clip(similarity, -1.0, 1.0)))
    
    return similarities


def find_most_similar(
    query_vec: List[float],
    vectors: List[List[float]],
    threshold: float = 0.95,
) -> tuple[int, float] | None:
    """
    Find the most similar vector from a list.
    
    Args:
        query_vec: Query vector
        vectors: List of vectors to search
        threshold: Minimum similarity threshold
        
    Returns:
        Tuple of (index, similarity) for most similar vector,
        or None if no vector meets threshold
    """
    similarities = batch_cosine_similarity(query_vec, vectors)
    
    if not similarities:
        return None
    
    max_idx = int(np.argmax(similarities))
    max_similarity = similarities[max_idx]
    
    if max_similarity >= threshold:
        return (max_idx, max_similarity)
    
    return None
