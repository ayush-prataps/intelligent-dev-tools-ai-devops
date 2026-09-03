import time
from typing import List
import httpx
from fastapi import HTTPException

from app.config import RETRIEVAL_SERVICE_URL, LLM_SERVICE_URL, SERVICE_TIMEOUT_SECONDS, MODEL_NAME
from app.schemas import OrchestrateResponse, TraceStep, RetrievedChunk


async def orchestrate_workflow(question: str, top_k: int = 3) -> OrchestrateResponse:
    """
    Orchestrates the multi-service RAG pipeline over HTTP REST APIs:
    1. Application Service (:8000) initializes request.
    2. Calls Retrieval Service (:8001) via HTTP POST /retrieve.
    3. Application Service constructs context-augmented prompt.
    4. Calls LLM Service (:8002) via HTTP POST /generate.
    5. Application Service assembles response with monotonic execution trace.
    """
    start_total = time.perf_counter()
    trace: List[TraceStep] = []

    # Step 1: Application Service receives request
    t1_start = time.perf_counter()
    trace.append(TraceStep(
        step=1,
        service="Application Service",
        action="Received question and initiated workflow",
        status="completed",
        elapsed_ms=round((time.perf_counter() - t1_start) * 1000, 2)
    ))

    # Step 2: HTTP POST to Retrieval Service
    t2_start = time.perf_counter()
    retrieve_url = f"{RETRIEVAL_SERVICE_URL}/retrieve"
    try:
        async with httpx.AsyncClient(timeout=SERVICE_TIMEOUT_SECONDS) as client:
            res_retrieval = await client.post(
                retrieve_url,
                json={"query": question, "top_k": top_k}
            )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Application Service failed to reach Retrieval Service at '{retrieve_url}'. "
                "Ensure Retrieval Service is running on port 8001."
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with Retrieval Service: {str(exc)}"
        )

    if res_retrieval.status_code != 200:
        raise HTTPException(
            status_code=res_retrieval.status_code,
            detail=f"Retrieval Service error: {res_retrieval.text}"
        )

    retrieval_data = res_retrieval.json()
    raw_chunks = retrieval_data.get("retrieved_chunks", [])
    retrieved_chunks = [RetrievedChunk(**c) for c in raw_chunks]

    trace.append(TraceStep(
        step=2,
        service="Retrieval Service",
        action=f"POST {retrieve_url}",
        status="completed",
        elapsed_ms=round((time.perf_counter() - t2_start) * 1000, 2)
    ))

    # Step 3: Application Service constructs augmented prompt
    t3_start = time.perf_counter()
    context_blocks = []
    for idx, c in enumerate(retrieved_chunks, start=1):
        context_blocks.append(
            f"[{idx}] Source: {c.doc_title} (Section: {c.section})\n{c.text}"
        )
    context_text = "\n\n".join(context_blocks)

    augmented_prompt = (
        "You are the official University Knowledge Assistant. "
        "Answer the student's question faithfully using the provided university policy context below.\n"
        "Ground your answer directly in the specific rules, percentages, and requirements provided in the context.\n"
        "If the context does not contain enough information to answer the question, state that clearly.\n\n"
        f"--- Retrieved Context ---\n{context_text}\n\n"
        f"Student Question: {question}\n\n"
        "Grounded Answer:"
    )

    trace.append(TraceStep(
        step=3,
        service="Application Service",
        action=f"Constructed augmented prompt using {len(retrieved_chunks)} context chunks",
        status="completed",
        elapsed_ms=round((time.perf_counter() - t3_start) * 1000, 2)
    ))

    # Step 4: HTTP POST to LLM Service
    t4_start = time.perf_counter()
    generate_url = f"{LLM_SERVICE_URL}/generate"
    try:
        async with httpx.AsyncClient(timeout=SERVICE_TIMEOUT_SECONDS) as client:
            res_llm = await client.post(
                generate_url,
                json={"prompt": augmented_prompt, "model": MODEL_NAME}
            )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Application Service failed to reach LLM Service at '{generate_url}'. "
                "Ensure LLM Service is running on port 8002."
            )
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Error communicating with LLM Service: {str(exc)}"
        )

    if res_llm.status_code != 200:
        raise HTTPException(
            status_code=res_llm.status_code,
            detail=f"LLM Service error: {res_llm.text}"
        )

    llm_data = res_llm.json()
    answer = llm_data.get("answer", "")

    trace.append(TraceStep(
        step=4,
        service="LLM Service",
        action=f"POST {generate_url}",
        status="completed",
        elapsed_ms=round((time.perf_counter() - t4_start) * 1000, 2)
    ))

    # Step 5: Application Service assembles final response
    t5_start = time.perf_counter()
    total_elapsed = round((time.perf_counter() - start_total) * 1000, 2)

    trace.append(TraceStep(
        step=5,
        service="Application Service",
        action="Assembled final orchestrated response with execution trace",
        status="completed",
        elapsed_ms=round((time.perf_counter() - t5_start) * 1000, 2)
    ))

    return OrchestrateResponse(
        question=question,
        answer=answer,
        retrieved_chunks=retrieved_chunks,
        orchestration_trace=trace,
        total_elapsed_ms=total_elapsed
    )
