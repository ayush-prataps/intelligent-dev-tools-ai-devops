import os
import json
import math
from typing import List, Dict, Any
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configuration
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
TIMEOUT_SECONDS: float = float(os.getenv("SERVICE_TIMEOUT_SECONDS", "120.0"))

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KNOWLEDGE_BASE_PATH = os.getenv(
    "KNOWLEDGE_BASE_PATH", os.path.join(BASE_DIR, "data", "knowledge_base.json")
)

app = FastAPI(
    title="Retrieval Service",
    description="Microservice responsible for query embeddings, pure-Python cosine similarity, and chunk retrieval",
    version="1.0.0"
)


class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=1, description="Query text to find relevant chunks for")
    top_k: int = Field(default=3, ge=1, le=10, description="Number of top chunks to retrieve")


class RetrievedChunk(BaseModel):
    chunk_id: str
    doc_id: str
    doc_title: str
    section: str
    similarity_score: float
    text: str


class RetrieveResponse(BaseModel):
    query: str
    top_k: int
    retrieved_chunks: List[RetrievedChunk]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two numerical vectors in pure Python."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))

    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0

    return dot_product / (norm1 * norm2)


async def get_query_embedding(text: str) -> List[float]:
    """Call Ollama /api/embeddings HTTP API to generate dense vector representation."""
    endpoint = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {"model": EMBEDDING_MODEL, "prompt": text}

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            res = await client.post(endpoint, json=payload)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Retrieval Service cannot reach Ollama at '{OLLAMA_BASE_URL}'."
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating embedding in Retrieval Service: {str(exc)}"
        )

    if res.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama embedding failed with status {res.status_code}: {res.text}"
        )

    data = res.json()
    embedding = data.get("embedding")
    if not embedding or not isinstance(embedding, list):
        raise HTTPException(status_code=502, detail="Invalid embedding response from Ollama")
    return embedding


def load_chunks() -> List[Dict[str, Any]]:
    """Load pre-computed knowledge base chunks from local disk."""
    if not os.path.exists(KNOWLEDGE_BASE_PATH):
        raise HTTPException(
            status_code=503,
            detail=f"Knowledge base file not found at '{KNOWLEDGE_BASE_PATH}'."
        )
    try:
        with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as f:
            kb = json.load(f)
            return kb.get("chunks", [])
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to read knowledge base file: {str(exc)}"
        )


@app.get("/health")
def health_check():
    """Health check for Retrieval Service."""
    return {"status": "ok", "service": "retrieval_service"}


@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve_chunks(payload: RetrieveRequest):
    """
    Perform vector similarity search:
    1. Generates query vector via Ollama.
    2. Reads chunks from knowledge_base.json.
    3. Computes pure Python cosine similarity.
    4. Returns top-K ranked chunks.
    """
    query_vector = await get_query_embedding(payload.query)
    chunks = load_chunks()

    scored = []
    for c in chunks:
        vec = c.get("embedding", [])
        score = cosine_similarity(query_vector, vec)
        scored.append(RetrievedChunk(
            chunk_id=c.get("chunk_id", ""),
            doc_id=c.get("doc_id", ""),
            doc_title=c.get("doc_title", ""),
            section=c.get("section", ""),
            similarity_score=round(score, 4),
            text=c.get("text", "")
        ))

    # Rank descending by score
    scored.sort(key=lambda x: x.similarity_score, reverse=True)
    top_chunks = scored[:payload.top_k]

    return RetrieveResponse(
        query=payload.query,
        top_k=payload.top_k,
        retrieved_chunks=top_chunks
    )
