import httpx
from fastapi import HTTPException

from app.config import OLLAMA_BASE_URL, MODEL_NAME, OLLAMA_TIMEOUT_SECONDS


async def generate_answer(prompt: str) -> str:
    """Send a prompt to Ollama's /api/generate HTTP endpoint and return the completed response text."""
    endpoint = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(endpoint, json=payload)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Cannot connect to Ollama at '{OLLAMA_BASE_URL}'. "
                "Ensure Ollama is installed and running locally."
            )
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=(
                f"Request to Ollama timed out after {OLLAMA_TIMEOUT_SECONDS}s. "
                "The model might still be processing or downloading."
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error communicating with Ollama: {str(exc)}"
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
            detail=f"Ollama returned error (status {response.status_code}): {error_detail}"
        )

    data = response.json()
    answer = data.get("response", "")
    return answer
