# Week 3 — Exercise 1: University Knowledge Assistant

## 1. Overview

The **University Knowledge Assistant** is a web-based educational tool designed to help students ask academic, course, and programming questions and receive answers from a local Large Language Model (**Code Llama 7B Instruct**) running via **Ollama**.

In **Exercise 1**, the application establishes the direct end-to-end integration without intermediate data stores:
`Browser UI → FastAPI Application → Ollama HTTP API → Code Llama`.

---

## 2. Architecture & Request Flow

```text
Student (Browser)
       │
       ▼
[Frontend UI] (HTML + CSS + Vanilla JS)
       │
       │  1. HTTP POST /api/ask { "question": "..." }
       ▼
[FastAPI Backend] (app/main.py)
       │
       │  2. Validates schema (AskRequest) & invokes service layer
       ▼
[Ollama Service] (app/services/ollama_service.py)
       │
       │  3. HTTP POST {OLLAMA_BASE_URL}/api/generate
       │     { "model": "codellama:7b-instruct", "prompt": "...", "stream": false }
       ▼
[Ollama HTTP API Server] (Default: http://localhost:11434)
       │
       │  4. Runs inference
       ▼
[Code Llama 7B Model] (codellama:7b-instruct)
       │
       │  5. Emits completed text
       ▼
[Ollama Service]
       │
       │  6. Extracts 'response' field
       ▼
[FastAPI Backend]
       │
       │  7. Returns HTTP 200 { "answer": "..." }
       ▼
[Frontend UI]
       │
       ▼
8. Hides loader and renders answer inside response card
```

---

## 3. Communication Breakdown

### A. Frontend → FastAPI
- **Protocol**: HTTP / REST.
- **Endpoint**: `POST /api/ask`.
- **Payload**: `{"question": "string"}`.
- **Client implementation**: Plain JavaScript `fetch()` API in `app/static/app.js`.
- **Handling**: JavaScript disables the submit button, displays an animated loading indicator, and listens for the JSON response. If an HTTP error is returned (e.g., 503 if Ollama is down), it displays an error alert banner to the user.

### B. FastAPI → Ollama
- **Protocol**: HTTP.
- **Endpoint**: `POST {OLLAMA_BASE_URL}/api/generate`.
- **Payload**:
  ```json
  {
    "model": "codellama:7b-instruct",
    "prompt": "...",
    "stream": false
  }
  ```
- **Service implementation**: `app/services/ollama_service.py` using `httpx.AsyncClient`.
- **Configuration**: Base URL is read dynamically from the `OLLAMA_BASE_URL` environment variable (default: `http://localhost:11434`), ensuring that when deployed in a VM or Docker environment in later exercises, no application code needs to be modified.

---

## 4. Project Structure

```text
week-3/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application & route definitions
│   ├── config.py            # Environment configuration with sensible defaults
│   ├── schemas.py           # Pydantic request & response models
│   ├── services/
│   │   ├── __init__.py
│   │   └── ollama_service.py # Ollama HTTP API client
│   └── static/
│       ├── index.html       # Web interface structure
│       ├── style.css        # Clean, professional styling
│       └── app.js           # Client-side API call and DOM management
├── requirements.txt         # Dependencies (fastapi, uvicorn, httpx)
├── .env.example             # Environment variable template
└── README.md                # Project documentation and guide
```

---

## 5. Setup & Running Locally

### Prerequisites
1. Python 3.10+
2. Ollama installed with the `codellama:7b-instruct` model pulled:
   ```bash
   ollama pull codellama:7b-instruct
   ```
3. Ollama server running:
   ```bash
   ollama serve
   ```

### Installation & Run Steps

1. **Navigate to the `week-3` directory**:
   ```bash
   cd week-3
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **(Optional) Configure environment variables**:
   ```bash
   # Default is http://localhost:11434
   export OLLAMA_BASE_URL="http://localhost:11434"
   ```

5. **Start the FastAPI application**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```

6. **Open in browser**:
   Visit [http://localhost:8000](http://localhost:8000) in your web browser.

---

## 6. API Endpoints

| Method | Endpoint | Description | Sample Response |
|---|---|---|---|
| `GET` | `/api/health` | Service health check | `{"status": "ok"}` |
| `POST` | `/api/ask` | Submit question to Code Llama | `{"answer": "A process is an executing program..."}` |
| `GET` | `/` | Serves the HTML frontend | HTML document |

---

## 7. Viva / Demonstration Talking Points

- **Modularity**: By placing the Ollama HTTP call inside `app/services/ollama_service.py`, the business logic is decoupled from FastAPI route handlers. When Exercise 2 introduces RAG and retrieval, the route handler simply delegates to a retrieval-augmented service without restructuring the web application.
- **Single-service deployment**: Mounting the `static` directory directly inside FastAPI eliminates the need for separate Node.js dev servers or complex Cross-Origin Resource Sharing (CORS) configurations in this stage.
- **Clean Configuration**: The application never hardcodes `localhost:11434`; it reads `OLLAMA_BASE_URL`, adhering to Twelve-Factor App principles for clean deployment across local, VM, and containerized targets.
