from typing import List
import httpx
from fastapi import HTTPException

from app.config import OLLAMA_BASE_URL, EMBEDDING_MODEL, OLLAMA_TIMEOUT_SECONDS


async def get_embedding(text: str) -> List[float]:
    """
    Generate a numerical embedding vector for the provided text using Ollama's /api/embeddings HTTP API.
    Does NOT use silent fallbacks; fails clearly if Ollama or the embedding model is unavailable.
    """
    endpoint = f"{OLLAMA_BASE_URL}/api/embeddings"
    payload = {
        "model": EMBEDDING_MODEL,
        "prompt": text
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(endpoint, json=payload)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Cannot connect to Ollama at '{OLLAMA_BASE_URL}'. "
                "Ensure Ollama is running ('ollama serve') before generating embeddings."
            )
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"Embedding request to Ollama timed out after {OLLAMA_TIMEOUT_SECONDS}s."
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error communicating with Ollama embedding API: {str(exc)}"
        )

    if response.status_code != 200:
        error_detail = response.text
        try:
            error_json = response.json()
            error_detail = error_json.get("error", error_detail)
        except Exception:
            pass
        raise HTTPException(
            status_code=502,
            detail=(
                f"Ollama embedding error (status {response.status_code}): {error_detail}. "
                f"Ensure the model is pulled ('ollama pull {EMBEDDING_MODEL}')."
            )
        )

    data = response.json()
    embedding = data.get("embedding")

    if not embedding or not isinstance(embedding, list):
        raise HTTPException(
            status_code=502,
            detail=f"Ollama returned an invalid or empty embedding for model '{EMBEDDING_MODEL}'."
        )

    return embedding
