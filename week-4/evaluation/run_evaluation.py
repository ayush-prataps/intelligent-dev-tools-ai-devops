import json
from pathlib import Path
import httpx
import time

BASE_DIR = Path(__file__).resolve().parents[2]
QUESTIONS_FILE = BASE_DIR / "week-4" / "data" / "evaluation_questions.json"
MODELS_FILE = BASE_DIR / "week-4" / "evaluation" / "models.json"

RETRIEVAL_URL = "http://127.0.0.1:8001"

with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    questions = json.load(f)

with open(MODELS_FILE, "r", encoding="utf-8") as f:
    models = json.load(f)["models"]

print(f"Loaded {len(questions)} questions")
print(f"Loaded {len(models)} models")

for model in models:
    print(f"- {model}")

question = questions[0]

retrieval_start = time.perf_counter()

retrieval_response = httpx.post(
    f"{RETRIEVAL_URL}/retrieve",
    json={"query": question["question"], "top_k": 3},
    timeout=120.0,
)

retrieval_latency_ms = (time.perf_counter() - retrieval_start) * 1000
retrieval_data = retrieval_response.json()

context = "\n\n".join(
    f"[{i}] Source: {chunk['doc_title']} (Section: {chunk['section']})\\n{chunk['text']}"
    for i, chunk in enumerate(retrieval_data["retrieved_chunks"], start=1)
)

prompt = f"""You are the official University Knowledge Assistant.
Answer the student's question faithfully using the provided university policy context below.
Ground your answer directly in the specific rules, percentages, and requirements provided in the context.
If the context does not contain enough information to answer the question, state that clearly.

--- Retrieved Context ---
{context}

Student Question: {question["question"]}
Grounded Answer:"""

LLM_URL = "http://127.0.0.1:8002"

print(f"\\nQuestion: {question['question']}")
print(f"Retrieval latency: {retrieval_latency_ms:.2f} ms")

for model in models:
    print(f"\\n--- {model} ---")

    start = time.perf_counter()

    response = httpx.post(
        f"{LLM_URL}/generate",
        json={"prompt": prompt, "model": model},
        timeout=180.0,
    )

    latency_ms = (time.perf_counter() - start) * 1000

    print(f"Status: {response.status_code}")
    print(f"Latency: {latency_ms:.2f} ms")
    print(json.dumps(response.json(), indent=2))
