# Week 3 — University Knowledge Assistant

## 1. Overview

The **University Knowledge Assistant** is an educational AI application designed to provide accurate answers to student questions regarding university regulations, course rules, academic policies, and campus facilities.

The project is built progressively across 5 exercises:
- **Exercise 1 (Completed)**: Direct LLM query flow (`Browser UI → FastAPI → Ollama → Code Llama → Browser`).
- **Exercise 2 (Completed)**: Knowledge Base creation (`Documents → Semantic Chunking → Ollama Embeddings → Vector Representation & Inspector UI`).
- **Exercise 3 (Completed)**: Retrieval-Augmented Generation (RAG pipeline) & Comparative Analysis.
- **Exercise 4 (Completed)**: Microservices Decomposition & HTTP Orchestration (`Application Gateway :8000 ➔ Retrieval Service :8001 ➔ LLM Service :8002`).
- **Exercise 5 (Completed)**: Docker Containerization & Multi-Service Compose Orchestration.

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

## 5. Running Locally (Without Docker)

### Prerequisites
Ensure Ollama is running with required models:
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

---

## 6. Exercise 5 — Dockerized Application

In Exercise 5, the three microservices are containerized using **Docker** and orchestrated via **Docker Compose** on an Ubuntu VM.

### Target Architecture

```text
User
  ↓
Application Container :8000
  ↓ HTTP (http://retrieval:8001)
Retrieval Container :8001
  ↓ HTTP (http://host.docker.internal:11434)
Ollama on Ubuntu VM :11434
  ↓
nomic-embed-text (Vector Embedding)
  ↓
knowledge_base.json / pure-Python Cosine Similarity
  ↓
Relevant Context Chunks
  ↓
Application Container :8000
  ↓ HTTP (http://llm:8002)
LLM Container :8002
  ↓ HTTP (http://host.docker.internal:11434)
Ollama on Ubuntu VM :11434
  ↓
Code Llama 7B (Inference)
  ↓
Application Container :8000
  ↓
User Response + Orchestration Trace
```

### Key Architectural Principles

1. **Decoupled Containers**:
   - `application`, `retrieval`, and `llm` run as lightweight, isolated Docker containers built from a clean `python:3.12-slim` base image.
2. **Ollama Kept Outside Docker on VM**:
   - Large language models (`codellama:7b-instruct`, 3.8 GB) and embedding weights require substantial RAM and disk.
   - Ollama runs directly as a host service on the Ubuntu VM (`11434`), avoiding heavy container layer caching, disk bloat, and memory duplication.
3. **Internal Container Networking & Service Discovery**:
   - Inside Docker Compose, containers communicate via Docker's embedded DNS:
     - Application reaches Retrieval at `http://retrieval:8001`.
     - Application reaches LLM at `http://llm:8002`.
     - `127.0.0.1` is **never** used for container-to-container traffic.
4. **Host Gateway Connectivity**:
   - To communicate with Ollama on the host VM, both the `retrieval` and `llm` containers use `extra_hosts`:
     ```yaml
     extra_hosts:
       - "host.docker.internal:host-gateway"
     ```
   - Target URL: `http://host.docker.internal:11434`.

---

### Docker Compose Commands

#### 1. Build Container Images
```bash
cd week-3
docker compose build
```

#### 2. Start Services in Background
```bash
docker compose up -d
```

#### 3. Inspect Running Containers
Verify all three containers are running:
```bash
docker compose ps
```

#### 4. Check Application Health Endpoints
Verify application and service health via HTTP:
```bash
# Application Service (:8000)
curl http://localhost:8000/api/health

# Retrieval Service (:8001)
curl http://localhost:8001/health

# LLM Service (:8002)
curl http://localhost:8002/health
```

#### 5. Execute Full Orchestration Request
```bash
curl -X POST http://localhost:8000/api/orchestrate \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the minimum attendance requirement and can it be condoned?","top_k":2}'
```

#### 6. Stop Containers
```bash
docker compose down
```

---

## 7. Running Automated Tests (Exercises 1–5)

Run the full verification suite across all 5 exercises:
```bash
cd week-3
./venv/bin/python test_exercise1.py
./venv/bin/python test_exercise2.py
./venv/bin/python test_exercise3.py
./venv/bin/python test_exercise4.py
./venv/bin/python test_exercise5.py
```

All 5 test suites will execute and pass (25/25 tests passing) with zero regressions.

---

## 8. Viva / Demonstration Talking Points

1. **Why is Ollama running directly on the VM instead of inside Docker?**
   - The Code Llama model is ~3.8 GB, and embedding weights require direct host memory allocation. Packaging the model inside a Docker image would drastically inflate image size, slow down deployment cycles, and exhaust the VM's disk and RAM.
2. **How do containers discover each other in Docker Compose?**
   - Docker Compose creates a default bridge network. Services use container service names (`retrieval`, `llm`) as hostnames with Docker's internal DNS resolving them to container IPs.
3. **How do Linux containers communicate with the host VM?**
   - Using `extra_hosts: ["host.docker.internal:host-gateway"]`, Docker maps `host.docker.internal` to the default network gateway of the host, enabling containerized services to communicate with `http://host.docker.internal:11434`.
4. **What does the Orchestrator do?**
   - The Application Service acts as a coordinator / workflow orchestrator. It receives user requests, queries the Retrieval Service over HTTP, synthesizes the context-augmented prompt, delegates completion to the LLM Service over HTTP, records real execution latencies using a monotonic clock, and returns the coordinated result to the client.
