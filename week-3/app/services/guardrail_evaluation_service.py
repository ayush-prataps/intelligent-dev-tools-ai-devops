from typing import Any, Dict, List, Optional

from app.services.guardrails import MIN_RETRIEVAL_SIMILARITY, GUARDRAIL_REFUSAL, validate_retrieval
from app.services.ollama_service import generate_answer_with_metrics
from app.services.rag_service import retrieve_rag_context


async def evaluate_guardrail_behavior(
    question: str,
    top_k: int = 3,
    models: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Compare unguarded generation with the retrieval-guarded decision.

    Retrieval is performed once so both paths inspect identical chunks.
    The guarded path never invokes an LLM when retrieval evidence is weak.
    """
    selected_models = models or [
        "codellama:7b-instruct",
        "phi3:mini",
        "qwen2.5:3b",
    ]
    context = await retrieve_rag_context(question, top_k=top_k)
    chunks = context["retrieved_chunks"]
    highest_similarity = max(
        (chunk.get("similarity_score", 0.0) for chunk in chunks),
        default=0.0,
    )
    guarded, refusal = validate_retrieval(chunks)

    unguarded_results: List[Dict[str, Any]] = []
    for model in selected_models:
        try:
            result = await generate_answer_with_metrics(
                prompt=context["augmented_prompt"],
                model=model,
            )
            result["status"] = "success"
        except Exception as exc:
            result = {
                "model": model,
                "status": "error",
                "error": str(exc),
            }
        unguarded_results.append(result)

    return {
        "question": question,
        "retrieved_chunks": chunks,
        "guardrail_threshold": MIN_RETRIEVAL_SIMILARITY,
        "highest_similarity": highest_similarity,
        "guardrail_passed": guarded,
        "guardrail_triggered": not guarded,
        "guarded_result": {
            "status": "allowed" if guarded else "rejected",
            "answer": None if guarded else refusal,
            "reason": None if guarded else "Retrieved context did not meet the similarity threshold",
        },
        "unguarded_results": unguarded_results,
    }
