import os
from typing import Optional
import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Configuration
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
DEFAULT_MODEL: str = os.getenv("MODEL_NAME", "codellama:7b-instruct")
TIMEOUT_SECONDS: float = float(os.getenv("SERVICE_TIMEOUT_SECONDS", "120.0"))

app = FastAPI(
    title="LLM Service",
    description="Microservice responsible for interacting with Ollama and Code Llama models",
    version="1.0.0"
)


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1, description="Prompt text to feed into the model")
    model: Optional[str] = Field(default=None, description="Model identifier to use")


class GenerateResponse(BaseModel):
    answer: str
    model: str


@app.get("/health")
def health_check():
    """Health check for LLM Service."""
    return {"status": "ok", "service": "llm_service"}


@app.post("/generate", response_model=GenerateResponse)
async def generate_completion(payload: GenerateRequest):
    """
    Generate model completion through Ollama:
    Calls Ollama POST /api/generate with stream=false and returns response text.
    """
    model_name = payload.model or DEFAULT_MODEL
    endpoint = f"{OLLAMA_BASE_URL}/api/generate"
    req_body = {
        "model": model_name,
        "prompt": payload.prompt,
        "stream": False
    }

    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_SECONDS) as client:
            response = await client.post(endpoint, json=req_body)
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=f"LLM Service cannot reach Ollama at '{OLLAMA_BASE_URL}'."
        )
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=504,
            detail=f"LLM generation timed out after {TIMEOUT_SECONDS}s."
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error in LLM Service: {str(exc)}"
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
            detail=f"Ollama returned error: {error_detail}"
        )

    data = response.json()
    answer = data.get("response", "")
    return GenerateResponse(answer=answer, model=model_name)
