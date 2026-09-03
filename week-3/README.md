# Week 3 — University Knowledge Assistant

## 1. Overview

The **University Knowledge Assistant** is an educational AI application designed to provide accurate answers to student questions regarding university regulations, course rules, academic policies, and campus facilities.

The project is built progressively across 5 exercises:
- **Exercise 1 (Completed)**: Direct LLM query flow (`Browser UI → FastAPI → Ollama → Code Llama → Browser`).
- **Exercise 2 (Completed)**: Knowledge Base creation (`Documents → Semantic Chunking → Ollama Embeddings → Vector Representation & Inspector UI`).
- **Exercise 3 (Completed)**: Retrieval-Augmented Generation (RAG pipeline) & Comparative Analysis.
- **Exercise 4 (Completed)**: Microservices Decomposition & HTTP Orchestration (`Application Gateway :8000 ➔ Retrieval Service :8001 ➔ LLM Service :8002`).
- **Exercise 5**: Docker containerization & VM deployment.

---

## 2. Exercise 4: Microservices & Orchestration Architecture

In Exercise 4, the application is decomposed into three independently runnable, decoupled FastAPI services communicating over HTTP REST APIs using `httpx`:

```text
Browser (Web Client)
       │
       │  POST /api/orchestrate { "question": "...", "top_k": 3 }
       ▼
[Application / Orchestrator Service] (Port :8000)
       │
       ├── 1. HTTP POST http://127.0.0.1:8001/retrieve
       │      Payload:  { "query": "...", "top_k": 3 }
       │      Response: { "retrieved_chunks": [...] }
       │      ↓
       │   [Retrieval Service] (Port :8001)
       │   - Generates query vector via Ollama nomic-embed-text
       │   - Computes pure Python Cosine Similarity over data/knowledge_base.json
       │   - Returns top-K ranked chunks
       │
       ├── 2. Constructs Context-Augmented Prompt
       │
       └── 3. HTTP POST http://127.0.0.1:8002/generate
              Payload:  { "prompt": "Context + Question...", "model": "codellama:7b-instruct" }
              Response: { "answer": "..." }
              ↓
           [LLM Service] (Port :8002)
           - Calls Ollama HTTP API (/api/generate)
           - Streams / returns Code Llama inference
       │
       ▼
Application Service assembles final response with Monotonic Execution Trace
       │
       ▼
Browser displays Grounded Answer + Live Orchestration Trace Timeline
```

---

## 3. Service Specifications & Ports

| Service | Port | Directory | Endpoints | Responsibility |
|---|---|---|---|---|
| **Application Service** | `8000` | `app/` | `GET /`<br>`POST /api/orchestrate`<br>`POST /api/ask`<br>`POST /api/rag`<br>`POST /api/compare` | Serves Web UI, acts as API Gateway, coordinates microservice pipeline, and records execution trace. |
| **Retrieval Service** | `8001` | `services/retrieval_service/` | `GET /health`<br>`POST /retrieve` | Standalone service: converts query to embeddings, executes cosine similarity over `knowledge_base.json`, returns ranked chunks. |
| **LLM Service** | `8002` | `services/llm_service/` | `GET /health`<br>`POST /generate` | Standalone service: dedicated interface to Ollama HTTP API for Code Llama completion. |

---

## 4. Orchestration Trace & Monotonic Timings

The Application Service records real execution timings using Python's monotonic clock (`time.perf_counter()`). Every response from `POST /api/orchestrate` includes an exact execution trace:

```json
{
  "question": "What is the minimum attendance requirement?",
  "answer": "The minimum attendance requirement is 75%...",
  "retrieved_chunks": [
    {
      "chunk_id": "attendance_policy_chunk_01",
      "doc_title": "University Attendance Policy",
      "section": "Minimum Attendance Requirement",
      "similarity_score": 0.825,
      "text": "..."
    }
  ],
  "orchestration_trace": [
    {
      "step": 1,
      "service": "Application Service",
      "action": "Received question and initiated workflow",
      "status": "completed",
      "elapsed_ms": 0.0
    },
    {
      "step": 2,
      "service": "Retrieval Service",
      "action": "POST http://127.0.0.1:8001/retrieve",
      "status": "completed",
      "elapsed_ms": 634.5
    },
    {
      "step": 3,
      "service": "Application Service",
      "action": "Constructed augmented prompt using 2 context chunks",
      "status": "completed",
      "elapsed_ms": 0.01
    },
    {
      "step": 4,
      "service": "LLM Service",
      "action": "POST http://127.0.0.1:8002/generate",
      "status": "completed",
      "elapsed_ms": 55497.0
    },
    {
      "step": 5,
      "service": "Application Service",
      "action": "Assembled final orchestrated response with execution trace",
      "status": "completed",
      "elapsed_ms": 0.0
    }
  ],
  "total_elapsed_ms": 56131.6
}
```

---

## 5. How to Run the Services

### Prerequisites
1. Ensure Ollama is running with required models:
   ```bash
   ollama serve
   ollama pull codellama:7b-instruct
   ollama pull nomic-embed-text
   ```

### Option A: Start All Services via Helper Script (Recommended)
Run the automated runner script which starts all three services simultaneously and handles clean shutdown on `Ctrl+C`:
```bash
cd week-3
./run_services.sh
```

### Option B: Start Services Individually (Separate Terminals)
```bash
cd week-3
source venv/bin/activate

# Terminal 1: Retrieval Service (:8001)
PYTHONPATH=. uvicorn services.retrieval_service.main:app --port 8001

# Terminal 2: LLM Service (:8002)
PYTHONPATH=. uvicorn services.llm_service.main:app --port 8002

# Terminal 3: Application Service (:8000)
PYTHONPATH=. uvicorn app.main:app --port 8000
```

Open `http://localhost:8000` in your web browser:
- **Tab 1 ("Direct LLM")**: Exercise 1 prompt interface (preserved).
- **Tab 2 ("RAG & Compare")**: Exercise 3 RAG & side-by-side comparison (preserved).
- **Tab 3 ("Orchestrated Flow")**: Exercise 4 live microservice topology cards, request flow diagram, and monotonic execution timeline.
- **Tab 4 ("Knowledge Base")**: Exercise 2 document browser & vector inspector (preserved).

---

## 6. Running Automated Tests

Run the full verification suite across all 4 exercises:
```bash
cd week-3
./venv/bin/python test_exercise1.py
./venv/bin/python test_exercise2.py
./venv/bin/python test_exercise3.py
./venv/bin/python test_exercise4.py
```

All 4 test suites will execute and pass with zero regressions.

---

## 7. Viva / Demonstration Talking Points

1. **Why decompose into microservices?**
   - **Independent Scaling & Deployment**: The retrieval pipeline (I/O and vector math) and the LLM inference (heavy compute/memory) can scale independently on different machines or containers in Exercise 5.
   - **Fault Isolation**: If the LLM service experiences heavy load, the Retrieval and Knowledge services remain operational.
2. **What does the Orchestrator do?**
   The Application Service acts as a coordinator / workflow orchestrator. It receives user requests, queries the Retrieval Service over HTTP, synthesizes the context-augmented prompt, delegates completion to the LLM Service over HTTP, records real execution latencies, and returns the coordinated result to the client.
3. **How is service communication implemented?**
   It uses real asynchronous HTTP REST calls via Python's `httpx` library. No microservice business logic is imported directly into `app/main.py`.
