# Week 3 — University Knowledge Assistant

## 1. Overview

The **University Knowledge Assistant** is an educational AI application designed to provide accurate answers to student questions regarding university regulations, course rules, academic policies, and campus facilities.

The project is built progressively across 5 exercises:
- **Exercise 1 (Completed)**: Direct LLM query flow (`Browser UI → FastAPI → Ollama → Code Llama → Browser`).
- **Exercise 2 (Completed)**: Knowledge Base creation (`Documents → Semantic Chunking → Ollama Embeddings → Vector Representation & Inspector UI`).
- **Exercise 3 (Completed)**: Retrieval-Augmented Generation (RAG pipeline) & Comparative Analysis (`Question → Query Embedding → Pure Python Cosine Similarity → Top-K Retrieval → Augmented Context → Code Llama → Grounded Answer`).
- **Exercise 4**: Service separation & modularization.
- **Exercise 5**: Docker containerization & VM deployment.

---

## 2. Exercise 3: Retrieval & RAG Pipeline

In Exercise 3, the application integrates retrieval into the question-answering workflow:
Instead of asking the LLM in isolation (where it may produce generic or hallucinated answers for university-specific rules), the system retrieves relevant policy chunks from `data/knowledge_base.json` using pure-Python cosine vector similarity and augments the model prompt with this factual context.

### Complete RAG Request Flow:
```text
Student Question: "What is the minimum attendance requirement and can it be condoned?"
                                 │
                                 ▼
                     [app/services/rag_service.py]
                                 │
      1. Query Vector Generation:│
         POST /api/embeddings    │ (via Ollama HTTP API)
         Model: nomic-embed-text │
                                 ▼
                         Query Vector (768D)
                                 │
      2. Vector Similarity Search:
         Cosine similarity against all 20 chunks in data/knowledge_base.json
                                 ▼
                      Ranked Chunks by Similarity:
        Rank 1: attendance_policy_chunk_01 (Score: 0.8020)
        Rank 2: attendance_policy_chunk_02 (Score: 0.7666)
                                 │
      3. Top-K Context Selection:
         [University Attendance Policy > Minimum Attendance Requirement] (75% rule)
         [University Attendance Policy > Condonation of Attendance Shortage] (65%-74.9% rule)
                                 │
      4. Augmented Prompt Synthesis:
         "Answer the question using ONLY the provided university policy context..."
                                 │
      5. Ollama Inference:
         POST /api/generate (codellama:7b-instruct)
                                 │
                                 ▼
                         Grounded Response
```

---

## 3. Pure Python Cosine Similarity

Vector similarity is calculated in `app/services/retrieval_service.py` without requiring external ML libraries or vector databases:

$$\text{Cosine Similarity}(\vec{u}, \vec{v}) = \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|} = \frac{\sum_{i=1}^{n} u_i v_i}{\sqrt{\sum_{i=1}^{n} u_i^2} \cdot \sqrt{\sum_{i=1}^{n} v_i^2}}$$

- **Dot Product ($\vec{u} \cdot \vec{v}$)**: Measures how much the two vectors point in the same direction.
- **Euclidean Norms ($\|\vec{u}\|, \|\vec{v}\|$)**: Normalizes for vector magnitudes.
- **Score**: Ranges from -1.0 to 1.0 (typically 0.0 to 1.0 for normalized text embeddings). Higher scores indicate closer semantic meaning.

---

## 4. Comparing Direct LLM vs. RAG

A core objective of Exercise 3 is demonstrating how responses differ when grounded context is provided versus when the LLM is queried blindly.

| Dimension | Direct LLM (Exercise 1) | RAG-Augmented LLM (Exercise 3) |
|---|---|---|
| **Input to LLM** | User question alone | User question + Top-K retrieved policy chunks |
| **Knowledge Source** | Model pre-training weights only | Local `knowledge_base.json` policy documents |
| **University Specifics** | Often gives generic advice or hallucinated criteria | Cites exact percentages (75% mandatory, 65% condonation) |
| **Authority References** | General speculation | Cites specific roles: Dean of Academic Affairs, Review Board |
| **Evidence / Auditability**| None; black box | Every retrieved chunk is inspectable with its similarity score |

> [!NOTE]
> RAG grounds generation in retrieved evidence and drastically reduces hallucinations for domain-specific tasks, but it does not mathematically guarantee 100% factual correctness. The model must still follow instructions faithfully.

---

## 5. API Endpoints

| Method | Endpoint | Exercise | Description |
|---|---|---|---|
| `GET` | `/api/health` | Ex 1 | Health check (`{"status": "ok"}`) |
| `POST` | `/api/ask` | Ex 1 | Direct LLM completion without retrieval |
| `GET` | `/api/knowledge/summary` | Ex 2 | Summary of documents, chunks, and vector dimension |
| `GET` | `/api/knowledge/documents` | Ex 2 | List raw markdown documents and content |
| `GET` | `/api/knowledge/chunks` | Ex 2 | List chunks with vector samples |
| `POST` | `/api/knowledge/index` | Ex 2 | Rebuild chunks and embeddings |
| `POST` | `/api/rag` | Ex 3 | End-to-end RAG question answering |
| `POST` | `/api/compare` | Ex 3 | Side-by-side comparison of Direct LLM vs RAG |

---

## 6. How to Run & Verify

### 1. Start Ollama and Verify Models
Ensure Ollama is running with both required models:
```bash
ollama serve
ollama list
# Ensure codellama:7b-instruct and nomic-embed-text are listed
```

### 2. Start the FastAPI Application
```bash
cd week-3
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Open `http://localhost:8000` in your browser:
- **Tab 1 ("Direct LLM")**: Ask questions without retrieval (Exercise 1).
- **Tab 2 ("RAG & Comparison")**: Ask questions with RAG or click **"Compare Direct vs RAG"** to observe side-by-side responses and retrieved context chunks (Exercise 3).
- **Tab 3 ("Knowledge Base")**: Inspect documents, chunks, and vectors (Exercise 2).

### 3. Run All Automated Test Suites
```bash
cd week-3
./venv/bin/python test_exercise1.py
./venv/bin/python test_exercise2.py
./venv/bin/python test_exercise3.py
```

---

## 7. Viva / Demonstration Talking Points

1. **How does the RAG pipeline work step-by-step?**
   The student asks a question $\rightarrow$ FastAPI sends the text to Ollama's `nomic-embed-text` $\rightarrow$ a 768-dimensional query vector is generated $\rightarrow$ pure Python computes cosine similarity against all 20 chunks $\rightarrow$ top-K chunks are retrieved $\rightarrow$ an augmented prompt is created with the evidence $\rightarrow$ Code Llama generates an answer grounded in the retrieved text.
2. **Why pure Python cosine similarity?**
   It eliminates the need for heavyweight vector databases (Chroma, Pinecone) or compiled C++ libraries during this stage, making the entire search process transparent and easily explainable in ~15 lines of code.
3. **How does RAG change the response?**
   Without RAG, Code Llama cannot know the specific rules of our university. With RAG, it references exact numbers (75% attendance rule, 65% condonation floor, 7-day medical certificate submission window, and Dean of Academic Affairs).
