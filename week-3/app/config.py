import os

# Base URL where Ollama HTTP service is listening
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")

# Target model for code and academic explanations (LLM generation)
MODEL_NAME: str = os.getenv("MODEL_NAME", "codellama:7b-instruct")

# Request timeout in seconds for Ollama API calls (LLM generation can take time on CPU)
OLLAMA_TIMEOUT_SECONDS: float = float(os.getenv("OLLAMA_TIMEOUT_SECONDS", "120.0"))

# Target model for vector embeddings
EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")

# Path to original university documents
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCUMENTS_DIR: str = os.getenv("DOCUMENTS_DIR", os.path.join(BASE_DIR, "data", "documents"))

# Path to persisted knowledge base JSON (chunks + vectors)
KNOWLEDGE_BASE_PATH: str = os.getenv(
    "KNOWLEDGE_BASE_PATH", os.path.join(BASE_DIR, "data", "knowledge_base.json")
)

# Exercise 4: Microservice endpoints
RETRIEVAL_SERVICE_URL: str = os.getenv(
    "RETRIEVAL_SERVICE_URL", "http://127.0.0.1:8001"
).rstrip("/")

LLM_SERVICE_URL: str = os.getenv(
    "LLM_SERVICE_URL", "http://127.0.0.1:8002"
).rstrip("/")

# Microservice HTTP communication timeout in seconds
SERVICE_TIMEOUT_SECONDS: float = float(os.getenv("SERVICE_TIMEOUT_SECONDS", "120.0"))
