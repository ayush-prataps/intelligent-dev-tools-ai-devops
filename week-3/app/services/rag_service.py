from typing import List, Dict, Any, Optional

from app.services.embedding_service import get_embedding
from app.services.retrieval_service import retrieve_top_k
from app.services.ollama_service import generate_answer, generate_answer_with_metrics


def build_augmented_prompt(question: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """Build a reusable RAG prompt from a question and retrieved chunks."""
    context_blocks = []
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        context_blocks.append(
            f"[{idx}] Source: {chunk.get('doc_title', 'Policy')} "
            f"(Section: {chunk.get('section', 'General')})\n"
            f"{chunk.get('text', '')}"
        )

    context_text = "\n\n".join(context_blocks)
    return (
        "You are the official University Knowledge Assistant. "
        "Answer the student's question faithfully using the provided university policy context below.\n"
        "Ground your answer in the specific rules, percentages, and requirements provided in the context.\n"
        "If the context does not contain enough information to answer the question, state that clearly.\n\n"
        f"--- Retrieved Context ---\n{context_text}\n\n"
        f"Student Question: {question}\n\n"
        "Grounded Answer:"
    )


async def retrieve_rag_context(
    question: str,
    top_k: int = 3,
) -> Dict[str, Any]:
    """Retrieve context and build the shared prompt without invoking an LLM."""
    query_vector = await get_embedding(question)
    retrieved_chunks = retrieve_top_k(query_vector, top_k=top_k)
    augmented_prompt = build_augmented_prompt(question, retrieved_chunks)

    return {
        "question": question,
        "retrieved_chunks": retrieved_chunks,
        "augmented_prompt": augmented_prompt,
    }


async def run_rag_pipeline(
    question: str,
    top_k: int = 3,
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """Run retrieval once and generate a grounded answer with the selected model."""
    context = await retrieve_rag_context(question, top_k=top_k)
    result = await generate_answer_with_metrics(
        prompt=context["augmented_prompt"],
        model=model,
    )

    return {
        **context,
        "answer": result["answer"],
        "model": result["model"],
        "prompt_eval_count": result.get("prompt_eval_count"),
        "eval_count": result.get("eval_count"),
        "total_duration": result.get("total_duration"),
        "load_duration": result.get("load_duration"),
        "prompt_eval_duration": result.get("prompt_eval_duration"),
        "eval_duration": result.get("eval_duration"),
        "latency_ms": result.get("latency_ms"),
        "grounding_summary": (
            f"Retrieved {len(context['retrieved_chunks'])} relevant policy chunks "
            "using cosine similarity."
        ),
    }


async def run_comparison(question: str, top_k: int = 3) -> Dict[str, Any]:
    """Run the legacy direct-LLM versus RAG comparison."""
    direct_answer = await generate_answer(question)
    rag_result = await run_rag_pipeline(question, top_k=top_k)

    return {
        "question": question,
        "direct_answer": direct_answer,
        "rag_answer": rag_result["answer"],
        "retrieved_chunks": rag_result["retrieved_chunks"],
    }
