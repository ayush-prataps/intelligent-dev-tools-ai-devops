import json
import os
import time
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles

from app.schemas import (
    AskRequest,
    AskResponse,
    RagRequest,
    RagResponse,
    CompareRequest,
    CompareResponse,
    OrchestrateRequest,
    OrchestrateResponse,
    RAGEvaluationRequest,
    RAGEvaluationResponse,
    GuardrailEvaluationRequest,
    GuardrailEvaluationResponse,
)
from app.services.ollama_service import generate_answer_with_metrics
from app.services.knowledge_service import (
    get_raw_documents,
    get_knowledge_summary,
    load_knowledge_base,
    build_knowledge_base,
)
from app.services.rag_service import (
    run_rag_pipeline,
    run_comparison,
    retrieve_rag_context,
)
from app.services.guardrail_evaluation_service import evaluate_guardrail_behavior
from app.services.orchestrator import orchestrate_workflow

app = FastAPI(
    title="University Knowledge Assistant",
    description="An AI assistant API powered by local models, embeddings, RAG retrieval, and orchestration",
    version="1.0.0",
)


@app.get("/api/health")
def health_check():
    return {"status": "ok"}


@app.post("/api/ask", response_model=AskResponse)
async def ask_question(payload: AskRequest):
    """Direct LLM endpoint retained as a baseline."""
    try:
        result = await generate_answer_with_metrics(
            prompt=payload.question,
            model=payload.model,
        )
        return AskResponse(**result)
    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise
        raise HTTPException(status_code=500, detail=f"Error generating answer: {exc}")


@app.get("/api/knowledge/summary")
def get_kb_summary():
    return get_knowledge_summary()


@app.get("/api/knowledge/documents")
def list_documents():
    return get_raw_documents()


@app.get("/api/knowledge/chunks")
def list_chunks(doc_id: Optional[str] = Query(None, description="Filter chunks by document ID")):
    kb = load_knowledge_base()
    if not kb:
        return {"chunks": [], "status": "not_indexed"}

    chunks = kb.get("chunks", [])
    if doc_id:
        chunks = [chunk for chunk in chunks if chunk.get("doc_id") == doc_id]

    inspected_chunks = []
    for chunk in chunks:
        vector = chunk.get("embedding", [])
        inspected_chunks.append({
            "chunk_id": chunk.get("chunk_id"),
            "doc_id": chunk.get("doc_id"),
            "doc_title": chunk.get("doc_title"),
            "section": chunk.get("section"),
            "text": chunk.get("text"),
            "char_count": chunk.get("char_count"),
            "word_count": chunk.get("word_count"),
            "vector_dimension": len(vector),
            "vector_sample": [round(value, 4) for value in vector[:5]],
            "full_vector": vector,
        })

    return {"status": "ready", "total": len(inspected_chunks), "chunks": inspected_chunks}


@app.post("/api/knowledge/index")
async def trigger_indexing():
    result = await build_knowledge_base()
    return {
        "status": "success",
        "message": "Knowledge base indexed successfully.",
        "summary": result.get("metadata"),
    }


@app.post("/api/rag", response_model=RagResponse)
async def ask_rag(payload: RagRequest):
    """Run the Week 3 RAG pipeline with an optional selected model."""
    result = await run_rag_pipeline(
        question=payload.question,
        top_k=payload.top_k,
        model=payload.model,
    )
    return RagResponse(**result)


@app.post("/api/rag/evaluate", response_model=RAGEvaluationResponse)
async def evaluate_rag_models(payload: RAGEvaluationRequest):
    """Retrieve context once, then evaluate each selected model on identical context and prompt."""
    models = payload.models or [
        "codellama:7b-instruct",
        "phi3:mini",
        "qwen2.5:3b",
    ]
    context = await retrieve_rag_context(payload.question, top_k=payload.top_k)
    results = []

    for model in models:
        start_time = time.perf_counter()
        try:
            generated = await generate_answer_with_metrics(
                prompt=context["augmented_prompt"],
                model=model,
            )
            generated["status"] = "success"
        except Exception as exc:
            generated = {
                "model": model,
                "status": "error",
                "error": str(exc),
            }
        generated["evaluation_elapsed_ms"] = round(
            (time.perf_counter() - start_time) * 1000,
            2,
        )
        results.append(generated)

    return RAGEvaluationResponse(
        question=payload.question,
        retrieved_chunks=context["retrieved_chunks"],
        results=results,
    )


@app.post("/api/rag/evaluate-guardrails", response_model=GuardrailEvaluationResponse)
async def evaluate_rag_guardrails(payload: GuardrailEvaluationRequest):
    """Compare unguarded model output with the retrieval guardrail decision."""
    result = await evaluate_guardrail_behavior(
        question=payload.question,
        top_k=payload.top_k,
        models=payload.models,
    )
    return GuardrailEvaluationResponse(**result)


@app.post("/api/compare", response_model=CompareResponse)
async def compare_answers(payload: CompareRequest):
    result = await run_comparison(payload.question, top_k=payload.top_k)
    return CompareResponse(**result)


@app.post("/api/orchestrate", response_model=OrchestrateResponse)
async def orchestrate_request(payload: OrchestrateRequest):
    return await orchestrate_workflow(payload.question, top_k=payload.top_k)


def _find_week4_file(filename: str, subfolder: str = "results") -> Optional[str]:
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "week-4", subfolder, filename)),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "static", "data", filename)),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "week4", filename)),
        os.path.abspath(os.path.join("/app", "week-4", subfolder, filename)),
    ]
    return next((path for path in candidates if os.path.exists(path)), None)


@app.get("/api/week4/metrics")
def get_week4_metrics():
    metrics_path = _find_week4_file("evaluation_metrics.json", "results")
    if metrics_path:
        with open(metrics_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"error": "Metrics file not found", "models": []}


@app.get("/api/week4/repository-analysis")
def get_week4_repo_analysis():
    repo_path = _find_week4_file("exercise6_repository_analysis.json", "results")
    if repo_path:
        with open(repo_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"error": "Repository analysis file not found", "results": []}


@app.get("/api/week4/guardrails")
def get_week4_guardrails():
    guard_path = _find_week4_file("ai_output_testing_results.json", "results")
    if guard_path:
        with open(guard_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"error": "Guardrails file not found", "tests": []}


@app.get("/api/week4/questions")
def get_week4_questions():
    questions_path = _find_week4_file("evaluation_questions.json", "data")
    if questions_path:
        with open(questions_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return {"error": "Questions file not found", "questions": []}


static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
