import time
from typing import Any, Dict, Optional

import httpx
from fastapi import HTTPException

from app.config import OLLAMA_BASE_URL, MODEL_NAME, OLLAMA_TIMEOUT_SECONDS


async def generate_answer_with_metrics(
    prompt: str,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Generate an Ollama response and return answer plus inference metrics."""
    selected_model = model or MODEL_NAME
    endpoint = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": selected_model,
        "prompt": prompt,
        "stream": False,
    }
    start_time = time.perf_counter()

    try:
        async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT_SECONDS) as client:
            response = await client.post(endpoint, json=payload)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"Cannot connect to Ollama at '{OLLAMA_BASE_URL}'.",
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"Request to Ollama timed out after {OLLAMA_TIMEOUT_SECONDS}s.",
        )
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Ollama request failed: {str(exc)}",
        )

    if response.status_code != 200:
        error_detail = response.text
        try:
            error_detail = response.json().get("error", error_detail)
        except Exception:
            pass
        raise HTTPException(
            status_code=502,
            detail=f"Ollama returned error (status {response.status_code}): {error_detail}",
        )

    data = response.json()
    latency_ms = (time.perf_counter() - start_time) * 1000

    return {
        "answer": data.get("response", ""),
        "model": data.get("model", selected_model),
        "prompt_eval_count": data.get("prompt_eval_count"),
        "eval_count": data.get("eval_count"),
        "total_duration": data.get("total_duration"),
        "load_duration": data.get("load_duration"),
        "prompt_eval_duration": data.get("prompt_eval_duration"),
        "eval_duration": data.get("eval_duration"),
        "latency_ms": round(latency_ms, 2),
    }


async def generate_answer(prompt: str, model: Optional[str] = None) -> str:
    """Backward-compatible helper returning only generated answer text."""
    result = await generate_answer_with_metrics(prompt=prompt, model=model)
    return result["answer"]
