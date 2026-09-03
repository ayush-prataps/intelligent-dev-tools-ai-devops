import os

# Base URL where Ollama HTTP service is listening
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")

# Target model for code and academic explanations
MODEL_NAME: str = os.getenv("MODEL_NAME", "codellama:7b-instruct")

# Request timeout in seconds for Ollama API calls (LLM generation can take time on CPU)
OLLAMA_TIMEOUT_SECONDS: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120.0"))
