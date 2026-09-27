"""Automated evaluation utilities for the Week 4 RAG dataset."""

import json
import os
import resource
import time
from collections import defaultdict
from typing import Any, Dict, List

from app.services.ollama_service import generate_answer_with_metrics
from app.services.rag_service import retrieve_rag_context
from app.services.guardrails import MIN_RETRIEVAL_SIMILARITY

DEFAULT_MODELS = ["codellama:7b-instruct", "phi3:mini", "qwen2.5:3b"]


def _dataset_path() -> str:
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "week-4", "data", "evaluation_questions.json")),
        os.path.abspath(os.path.join("/app", "week-4", "data", "evaluation_questions.json")),
    ]
    for candidate in candidates:
        if os.path.exists(candidate):
            return candidate
    raise FileNotFoundError("Week 4 evaluation_questions.json was not found")


def load_evaluation_questions() -> List[Dict[str, Any]]:
    with open(_dataset_path(), "r", encoding="utf-8") as file:
        return json.load(file)


def _terms(text: str) -> set[str]:
    import re
    stopwords = {"the", "and", "for", "with", "from", "that", "this", "what", "how", "are", "can", "does", "into", "their"}
    return {word for word in re.findall(r"[a-zA-Z0-9]+", text.lower()) if len(word) >= 4 and word not in stopwords}


def _score_answer(answer: str, expected: str, context: str) -> Dict[str, float]:
    answer_terms = _terms(answer)
    expected_terms = _terms(expected)
    context_terms = _terms(context)

    expected_coverage = len(answer_terms & expected_terms) / max(1, len(expected_terms))
    relevance = len(answer_terms & _terms(context)) / max(1, len(answer_terms))
    grounding = len(answer_terms & context_terms) / max(1, len(answer_terms))

    return {
        "correctness": round(min(1.0, expected_coverage), 4),
        "relevance": round(min(1.0, relevance), 4),
        "grounding": round(min(1.0, grounding), 4),
    }


def _aggregate(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    successful = [item for item in results if item.get("status") == "success"]
    if not successful:
        return {"question_count": len(results), "successful_count": 0}

    fields = ["correctness", "relevance", "grounding", "retrieval_quality", "latency_ms"]
    averages = {
        field: round(sum(float(item.get(field, 0.0)) for item in successful) / len(successful), 4)
        for field in fields
    }
    return {
        "question_count": len(results),
        "successful_count": len(successful),
        "failed_count": len(results) - len(successful),
        "averages": averages,
        "guardrail_triggered_count": sum(1 for item in successful if item.get("guardrail_triggered")),
    }


async def evaluate_dataset(models: List[str] | None = None, limit: int | None = None) -> Dict[str, Any]:
    selected_models = models or DEFAULT_MODELS
    questions = load_evaluation_questions()
    if limit:
        questions = questions[:limit]

    by_model: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    system_before = resource.getrusage(resource.RUSAGE_SELF)
    overall_start = time.perf_counter()

    for item in questions:
        context = await retrieve_rag_context(item["question"], top_k=3)
        chunks = context["retrieved_chunks"]
        highest_similarity = max((float(chunk.get("similarity_score", 0.0)) for chunk in chunks), default=0.0)
        context_text = " ".join(chunk.get("text", "") for chunk in chunks)
        retrieval_quality = 1.0 if highest_similarity >= MIN_RETRIEVAL_SIMILARITY else highest_similarity / MIN_RETRIEVAL_SIMILARITY
        expected_answer = item.get("expected_answer") or "The provided knowledge base does not contain information about hostel room allocation."

        for model in selected_models:
            started = time.perf_counter()
            try:
                generated = await generate_answer_with_metrics(prompt=context["augmented_prompt"], model=model)
                answer = generated.get("answer", "")
                scores = _score_answer(answer, expected_answer, context_text)
                generated.update({
                    "id": item["id"],
                    "category": item.get("category"),
                    "status": "success",
                    "retrieval_quality": round(retrieval_quality, 4),
                    "highest_similarity": round(highest_similarity, 4),
                    "guardrail_triggered": highest_similarity < MIN_RETRIEVAL_SIMILARITY,
                    **scores,
                    "evaluation_elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                })
            except Exception as exc:
                generated = {
                    "id": item["id"],
                    "category": item.get("category"),
                    "model": model,
                    "status": "error",
                    "error": str(exc),
                    "evaluation_elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
                }
            by_model[model].append(generated)

    system_after = resource.getrusage(resource.RUSAGE_SELF)
    return {
        "dataset": "week-4/data/evaluation_questions.json",
        "models": selected_models,
        "question_count": len(questions),
        "elapsed_ms": round((time.perf_counter() - overall_start) * 1000, 2),
        "resource_usage": {
            "user_cpu_seconds": round(system_after.ru_utime - system_before.ru_utime, 4),
            "system_cpu_seconds": round(system_after.ru_stime - system_before.ru_stime, 4),
            "max_rss_kb": system_after.ru_maxrss,
        },
        "model_comparison": {
            model: {"aggregate": _aggregate(results), "results": results}
            for model, results in by_model.items()
        },
    }
