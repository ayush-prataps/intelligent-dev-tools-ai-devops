import json
import sys
import time
from pathlib import Path

import httpx


BASE_DIR = Path(__file__).resolve().parents[2]
QUESTIONS_FILE = BASE_DIR / "week-4" / "data" / "evaluation_questions.json"
MODELS_FILE = BASE_DIR / "week-4" / "evaluation" / "models.json"
RESULTS_DIR = BASE_DIR / "week-4" / "results"
RETRIEVAL_RESULTS_FILE = RESULTS_DIR / "retrieval_results.json"

RETRIEVAL_URL = "http://127.0.0.1:8001"
LLM_URL = "http://127.0.0.1:8002"


def load_questions():
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_models():
    with open(MODELS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)["models"]


def build_prompt(question, retrieved_chunks):
    context = "\n\n".join(
        f"[{i}] Source: {chunk['doc_title']} "
        f"(Section: {chunk['section']})\n{chunk['text']}"
        for i, chunk in enumerate(retrieved_chunks, start=1)
    )

    return f"""You are the official University Knowledge Assistant.
Answer the student's question faithfully using the provided university policy context below.
Ground your answer directly in the specific rules, percentages, and requirements provided in the context.
If the context does not contain enough information to answer the question, state that clearly.

--- Retrieved Context ---
{context}

Student Question: {question["question"]}
Grounded Answer:"""


def run_retrieval(questions):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    results = []

    print(f"Retrieving context for {len(questions)} questions...")

    for question in questions:
        question_id = question["id"]

        print(f"\n[{question_id}] {question['question']}")

        start = time.perf_counter()

        try:
            response = httpx.post(
                f"{RETRIEVAL_URL}/retrieve",
                json={"query": question["question"], "top_k": 3},
                timeout=120.0,
            )

            latency_ms = (time.perf_counter() - start) * 1000
            response.raise_for_status()

            data = response.json()
            retrieved_chunks = data["retrieved_chunks"]

            result = {
                "question_id": question_id,
                "category": question["category"],
                "question": question["question"],
                "expected_answer": question["expected_answer"],
                "expected_source": question["expected_source"],
                "expected_section": question["expected_section"],
                "retrieval_latency_ms": round(latency_ms, 2),
                "retrieved_chunks": retrieved_chunks,
                "error": None,
            }

            print(f"  Retrieval: {latency_ms:.2f} ms")
            print(f"  Chunks: {len(retrieved_chunks)}")

        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000

            result = {
                "question_id": question_id,
                "category": question["category"],
                "question": question["question"],
                "expected_answer": question["expected_answer"],
                "expected_source": question["expected_source"],
                "expected_section": question["expected_section"],
                "retrieval_latency_ms": round(latency_ms, 2),
                "retrieved_chunks": [],
                "error": str(exc),
            }

            print(f"  Retrieval ERROR after {latency_ms:.2f} ms — {exc}")

        results.append(result)

        # Save after every question so a later failure does not
        # destroy the completed retrieval work.
        with open(RETRIEVAL_RESULTS_FILE, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    print(
        f"\nSaved {len(results)} retrieval records to "
        f"{RETRIEVAL_RESULTS_FILE}"
    )


def result_filename(model):
    safe_name = model.replace(":", "_").replace("/", "_")
    return RESULTS_DIR / f"{safe_name}_results.json"


def run_model(model, models):
    if model not in models:
        raise SystemExit(
            f"Unknown model '{model}'. Available models: {', '.join(models)}"
        )

    if not RETRIEVAL_RESULTS_FILE.exists():
        raise SystemExit(
            "retrieval_results.json not found. Run the retrieval phase first."
        )

    with open(RETRIEVAL_RESULTS_FILE, "r", encoding="utf-8") as f:
        retrieval_results = json.load(f)

    output_file = result_filename(model)
    results = []

    print(f"Loaded {len(retrieval_results)} retrieval records")
    print(f"Evaluating model: {model}")

    for retrieval in retrieval_results:
        question_id = retrieval["question_id"]

        print(f"\n[{question_id}] {retrieval['question']}")

        if retrieval["error"] is not None:
            result = {
                **retrieval,
                "model": model,
                "answer": "",
                "llm_latency_ms": None,
                "prompt_eval_count": None,
                "eval_count": None,
                "total_duration_ns": None,
            }

            print("  Skipped: retrieval failed")

        else:
            question = {
                "question": retrieval["question"],
            }

            prompt = build_prompt(
                question,
                retrieval["retrieved_chunks"],
            )

            start = time.perf_counter()

            try:
                response = httpx.post(
                    f"{LLM_URL}/generate",
                    json={
                        "prompt": prompt,
                        "model": model,
                    },
                    timeout=180.0,
                )

                latency_ms = (time.perf_counter() - start) * 1000
                response.raise_for_status()

                llm_data = response.json()

                result = {
                    **retrieval,
                    "model": model,
                    "answer": llm_data.get("answer", ""),
                    "error": None,
                    "llm_latency_ms": round(latency_ms, 2),
                    "prompt_eval_count": llm_data.get("prompt_eval_count"),
                    "eval_count": llm_data.get("eval_count"),
                    "total_duration_ns": llm_data.get("total_duration"),
                }

                print(
                    f"  {model}: {latency_ms:.2f} ms, "
                    f"{llm_data.get('prompt_eval_count')} prompt tokens, "
                    f"{llm_data.get('eval_count')} output tokens"
                )

            except Exception as exc:
                latency_ms = (time.perf_counter() - start) * 1000

                result = {
                    **retrieval,
                    "model": model,
                    "answer": "",
                    "error": str(exc),
                    "llm_latency_ms": round(latency_ms, 2),
                    "prompt_eval_count": None,
                    "eval_count": None,
                    "total_duration_ns": None,
                }

                print(
                    f"  {model}: ERROR after "
                    f"{latency_ms:.2f} ms — {exc}"
                )

        results.append(result)

        # Save after every question.
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(results)} evaluation records to {output_file}")


def main():
    questions = load_questions()
    models = load_models()

    if len(sys.argv) != 2:
        raise SystemExit(
            "Usage:\n"
            "  python week-4/evaluation/run_evaluation.py retrieve\n"
            "  python week-4/evaluation/run_evaluation.py <model>"
        )

    command = sys.argv[1]

    if command == "retrieve":
        run_retrieval(questions)
    else:
        run_model(command, models)


if __name__ == "__main__":
    main()
