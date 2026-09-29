"""
ShopSense Vector Search & Semantic Recommendation Engine Module
Generates dense vector embeddings for products & user behavior, storing them in an in-memory Vector Index
to provide highly contextual semantic search and recommendations via Cosine Similarity calculations.
"""
from typing import List, Dict, Any
import math
import re

def generate_text_embedding_vector(text: str, vector_dim: int = 16) -> List[float]:
    """
    Generates a normalized dense vector embedding (16-dimensional representation) for text content.
    Simulates a Vector DB embedding generator (e.g. pgvector / OpenAI / Vertex embeddings).
    """
    words = re.findall(r'\w+', text.lower())
    vec = [0.0] * vector_dim
    if not words:
        return vec

    for idx, w in enumerate(words):
        hash_val = sum(ord(c) for c in w)
        dim_idx = hash_val % vector_dim
        vec[dim_idx] += 1.0 / len(words)

    # Normalize vector to unit length (L2 norm)
    magnitude = math.sqrt(sum(v**2 for v in vec)) or 1.0
    return [round(v / magnitude, 4) for v in vec]

def cosine_similarity_dense_vectors(vec1: List[float], vec2: List[float]) -> float:
    """Calculates cosine similarity between two dense embedding vectors."""
    if len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(v1 * v2 for v1, v2 in zip(vec1, vec2))
    mag1 = math.sqrt(sum(v**2 for v in vec1)) or 1.0
    mag2 = math.sqrt(sum(v**2 for v in vec2)) or 1.0

    sim = dot_product / (mag1 * mag2)
    return max(min(round(sim, 4), 1.0), 0.0)

def semantic_vector_search(query: str, products: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Performs semantic vector search against product embeddings in vector space.
    Returns products ranked by Cosine Similarity match confidence.
    """
    if not query.strip() or not products:
        return []

    # Generate query vector embedding
    query_vector = generate_text_embedding_vector(query)
    results = []

    for p in products:
        # Build composite product document
        p_text = f"{p.get('name', '')} {p.get('category', '')} {p.get('ai_description', '')}"
        product_vector = generate_text_embedding_vector(p_text)

        # Calculate Vector Cosine Similarity
        cos_sim = cosine_similarity_dense_vectors(query_vector, product_vector)

        # Keyword alignment boost
        query_words = set(re.findall(r'\w+', query.lower()))
        p_words = set(re.findall(r'\w+', p_text.lower()))
        overlap = len(query_words & p_words)
        if overlap > 0:
            cos_sim = min(cos_sim + (overlap * 0.25), 1.0)

        results.append({
            "product_id": p.get("id"),
            "name": p.get("name"),
            "category": p.get("category"),
            "price": p.get("price"),
            "stock": p.get("stock"),
            "image_url": p.get("image_url"),
            "ai_description": p.get("ai_description"),
            "vector_embedding_dim": len(product_vector),
            "similarity_score": round(cos_sim, 4),
            "match_confidence": f"{round(cos_sim * 100)}%"
        })

    # Sort descending by vector similarity
    results_sorted = sorted(results, key=lambda x: x["similarity_score"], reverse=True)
    return results_sorted[:top_k]
