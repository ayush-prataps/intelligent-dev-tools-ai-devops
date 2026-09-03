import math
from typing import List, Dict, Any
from fastapi import HTTPException

from app.services.knowledge_service import load_knowledge_base


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Compute cosine similarity between two numerical vectors using pure Python.
    
    Mathematical Definition:
        Cosine Similarity = (vec1 · vec2) / (||vec1|| * ||vec2||)
        
        Where:
        - Dot Product (vec1 · vec2) = ∑ (vec1[i] * vec2[i])
        - Euclidean Norm ||v||     = √(∑ (v[i]²))
        
    Returns:
        A float between -1.0 and 1.0 (typically 0.0 to 1.0 for normalized text embeddings),
        where 1.0 means identical directional semantics.
    """
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    return dot_product / (norm1 * norm2)


def retrieve_top_k(query_vector: List[float], top_k: int = 3) -> List[Dict[str, Any]]:
    """
    Perform vector similarity search across all stored chunks in knowledge_base.json.
    
    Pipeline:
    1. Load pre-computed chunk vectors from local knowledge base.
    2. Compute cosine similarity between query vector and every chunk vector.
    3. Rank all chunks in descending order of similarity score.
    4. Return top-K ranked chunks formatted with metadata and scores.
    """
    kb = load_knowledge_base()
    if not kb or not kb.get("chunks"):
        raise HTTPException(
            status_code=503,
            detail=(
                "Knowledge base is empty or not yet generated. "
                "Please run Exercise 2 indexing before performing RAG retrieval."
            )
        )

    scored_chunks = []
    for chunk in kb["chunks"]:
        chunk_vector = chunk.get("embedding", [])
        score = cosine_similarity(query_vector, chunk_vector)
        scored_chunks.append({
            "chunk_id": chunk.get("chunk_id", ""),
            "doc_id": chunk.get("doc_id", ""),
            "doc_title": chunk.get("doc_title", ""),
            "section": chunk.get("section", ""),
            "similarity_score": round(score, 4),
            "text": chunk.get("text", "")
        })

    # Sort descending by similarity score
    scored_chunks.sort(key=lambda x: x["similarity_score"], reverse=True)

    # Return top_k
    return scored_chunks[:top_k]
