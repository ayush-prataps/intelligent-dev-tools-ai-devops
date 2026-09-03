# Week 3 — University Knowledge Assistant

## 1. Overview

The **University Knowledge Assistant** is an educational AI application designed to provide accurate answers to student questions regarding university regulations, course rules, academic policies, and campus facilities.

The project is built progressively across 5 exercises:
- **Exercise 1 (Completed)**: Direct LLM query flow (`Browser UI → FastAPI → Ollama → Code Llama → Browser`).
- **Exercise 2 (Completed)**: Knowledge Base creation (`Documents → Semantic Chunking → Ollama Embeddings → Vector Representation & Inspector UI`).
- **Exercise 3**: Retrieval-Augmented Generation (RAG pipeline).
- **Exercise 4**: Service separation & modularization.
- **Exercise 5**: Docker containerization & VM deployment.

---

## 2. Exercise 2: Knowledge Base Stage

In Exercise 2, raw policy documents are processed into structured, vector-embedded knowledge chunks without requiring a heavyweight vector database.

### The Pipeline Flow:
```text
Raw University Documents (5 Markdown files)
                    │
                    ▼
[Semantic-Aware Chunking] (app/services/chunking_service.py)
  - Preserves [Doc Title > Section Name] context
  - Respects natural paragraph and sentence boundaries
                    │
                    ▼
[Embedding Generation] (app/services/embedding_service.py)
  - HTTP POST {OLLAMA_BASE_URL}/api/embeddings
  - Model: nomic-embed-text
  - Dynamically determines vector dimension (768D)
                    │
                    ▼
[Local Vector Storage] (data/knowledge_base.json)
  - Human-readable JSON containing chunks, metadata, and numerical vector floats
                    │
                    ▼
[FastAPI Inspection API & UI]
  - GET /api/knowledge/summary
  - GET /api/knowledge/documents
  - GET /api/knowledge/chunks
  - Interactive web UI inspector with vector sample previews
```

---

## 3. University Knowledge Documents

Stored under `data/documents/`:
1. `academic_policies.md`: Degree credits, course registration, prerequisite rules, academic probation, and Honors/Minor degrees.
2. `attendance_policy.md`: 75% minimum attendance rule, medical condonation procedures, debarment criteria, and ERP monitoring.
3. `examination_rules.md`: Examination hall entry, prohibited electronics, 10-point CGPA grading scale, and supplementary exams.
4. `leave_policy.md`: Casual leave allowances, certified medical leave guidelines, On-Duty (OD) sports/competition leave, and semester withdrawal.
5. `campus_facilities.md`: Central library hours and borrowing limits, GPU computing labs, innovation maker space, and sports arena rules.

---

## 4. Semantic-Aware Chunking Strategy

Unlike naive character slicing (which cuts mid-word or separates related sentences), the chunker in `app/services/chunking_service.py`:
1. **Parses Heading Hierarchy**: Treats `# Document Title` and `## Section Heading` as logical units.
2. **Context Preservation**: Prepends `[Document Title > Section Name]` to every chunk so the language model always knows what rule the chunk belongs to.
3. **Natural Boundaries**: Splits large sections only at paragraph (`\n\n`) or sentence ends.
4. **Structured Metadata**: Each chunk stores `chunk_id`, `doc_id`, `section`, `text`, `char_count`, and `word_count`.

---

## 5. Embeddings & Dynamic Vector Representation

- **Embedding Model**: `nomic-embed-text` via Ollama's `/api/embeddings` HTTP endpoint.
- **Dynamic Dimension**: Vector dimension is **not** hard-coded. It is dynamically detected from the actual response (`len(vector) = 768`) and saved in `knowledge_base.json` metadata.
- **Strict Error Handling**: No silent mock fallbacks during real generation. If Ollama is offline or the model is not installed, the system immediately returns a clear error explaining that `ollama serve` or `ollama pull nomic-embed-text` is required.
- **Storage**: Chunks and their numerical vectors are stored in `data/knowledge_base.json`.

---

## 6. Project Structure

```text
week-3/
├── app/
│   ├── __init__.py
│   ├── main.py              # Endpoints: /api/health, /api/ask, /api/knowledge/*
│   ├── config.py            # Environment configuration (URLs, models, data paths)
│   ├── schemas.py           # Pydantic validation schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ollama_service.py     # Code Llama LLM client (Exercise 1)
│   │   ├── chunking_service.py   # Semantic Markdown chunker (Exercise 2)
│   │   ├── embedding_service.py  # Real Ollama embedding client (Exercise 2)
│   │   └── knowledge_service.py  # Document & KB orchestrator (Exercise 2)
│   └── static/
│       ├── index.html       # Web UI with tab navigation (Ask Assistant & Knowledge Base)
│       ├── style.css        # Responsive styling with summary cards, doc preview, and chunk cards
│       └── app.js           # Client-side API calls, tab switching, and vector inspection
├── data/
│   ├── documents/           # 5 university policy documents
│   └── knowledge_base.json  # Persisted chunks with 768D numerical vectors
├── requirements.txt         # fastapi, uvicorn[standard], httpx
├── .env.example             # Template for configuration
├── .gitignore               # Excludes venv/ and pycache
├── test_exercise1.py        # Exercise 1 test suite
├── test_exercise2.py        # Exercise 2 test suite
└── README.md                # Documentation & viva guide
```

---

## 7. How to Run Locally

### 1. Prerequisites
- Python 3.10+
- Ollama installed and running (`ollama serve`)
- Required models:
  ```bash
  ollama pull codellama:7b-instruct
  ollama pull nomic-embed-text
  ```

### 2. Setup & Run Application
```bash
cd week-3
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` in your web browser:
- **Tab 1 ("Ask Assistant")**: Ask questions directly to Code Llama (Exercise 1).
- **Tab 2 ("Knowledge Base")**: Inspect documents, chunks, and embedding vectors, or trigger re-indexing (Exercise 2).

### 3. Run Automated Tests
```bash
# Run Exercise 1 regression suite
./venv/bin/python test_exercise1.py

# Run Exercise 2 test suite
./venv/bin/python test_exercise2.py
```

---

## 8. Viva & Demonstration Talking Points

1. **Why Ollama for embeddings?**
   It eliminates the need to install 1.5+ GB of PyTorch and Hugging Face dependencies in Python, keeping the app lightweight and perfectly suited for the 6GB CPU-only Ubuntu VM used in later exercises.
2. **Why semantic chunking over fixed-size character chunking?**
   Fixed-character chunking splits words and cuts sentences in half, causing context loss. Our chunker groups text by Markdown headings and paragraphs, prepending context tags (`[Document > Section]`).
3. **Why JSON vector storage instead of a vector database?**
   In this stage, a vector database adds unnecessary operational complexity. Storing vectors in `knowledge_base.json` makes the embedding arrays 100% transparent and inspectable in real-time. In Exercise 3, we can easily compute cosine similarity directly over this file.
4. **Dynamic Dimension Handling**:
   The embedding dimension is dynamically measured from the returned vector (`len(embedding) = 768`) rather than hardcoded, ensuring flexibility if different embedding models are used.
