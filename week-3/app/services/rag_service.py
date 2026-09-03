from typing import List, Dict, Any

from app.services.embedding_service import get_embedding
from app.services.retrieval_service import retrieve_top_k
from app.services.ollama_service import generate_answer


def build_augmented_prompt(question: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
    """
    Construct a context-augmented prompt instructing Code Llama to answer
    using the retrieved university policy evidence.
    """
    context_blocks = []
    for idx, chunk in enumerate(retrieved_chunks, start=1):
        context_blocks.append(
            f"[{idx}] Source: {chunk.get('doc_title', 'Policy')} (Section: {chunk.get('section', 'General')})\n"
            f"{chunk.get('text', '')}"
        )
    context_text = "\n\n".join(context_blocks)

    prompt = (
        "You are the official University Knowledge Assistant. "
        "Answer the student's question faithfully using the provided university policy context below.\n"
        "Ground your answer in the specific rules, percentages, and requirements provided in the context.\n"
        "If the context does not contain enough information to answer the question, state that clearly.\n\n"
        f"--- Retrieved Context ---\n{context_text}\n\n"
        f"Student Question: {question}\n\n"
        "Grounded Answer:"
    )
    return prompt


async def run_rag_pipeline(question: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Execute the end-to-end RAG pipeline:
    Question -> Query Embedding -> Cosine Similarity -> Top-K Retrieval -> Context Augmentation -> Code Llama.
    """
    # 1. Generate query embedding using Ollama nomic-embed-text
    query_vector = await get_embedding(question)

    # 2. Retrieve top-k relevant chunks by vector cosine similarity
    retrieved_chunks = retrieve_top_k(query_vector, top_k=top_k)

    # 3. Build context-augmented prompt
    augmented_prompt = build_augmented_prompt(question, retrieved_chunks)

    # 4. Generate grounded response using Code Llama
    answer = await generate_answer(augmented_prompt)

    return {
        "question": question,
        "answer": answer,
        "retrieved_chunks": retrieved_chunks,
        "grounding_summary": f"Retrieved {len(retrieved_chunks)} relevant policy chunks using cosine similarity."
    }


async def run_comparison(question: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Execute both Direct LLM and RAG pipelines on the same question
    to demonstrate the difference when relevant context is provided.
    """
    # 1. Direct LLM: raw prompt without retrieval
    direct_answer = await generate_answer(question)

    # 2. RAG pipeline: retrieval-augmented generation
    rag_result = await run_rag_pipeline(question, top_k=top_k)

    return {
        "question": question,
        "direct_answer": direct_answer,
        "rag_answer": rag_result["answer"],
        "retrieved_chunks": rag_result["retrieved_chunks"]
    }
