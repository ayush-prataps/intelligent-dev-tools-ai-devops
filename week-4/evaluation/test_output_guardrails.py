import json
import re
from pathlib import Path

import requests


BASE_URL = "http://localhost:8000/api/orchestrate"
DATASET_PATH = Path("week-4/data/evaluation_questions.json")
RESULTS_PATH = Path("week-4/results/ai_output_testing_results.json")

REFUSAL_TEXT = (
    "I'm unable to answer this question from the available university "
    "knowledge base."
)

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "how", "in", "is", "it", "of", "on", "or", "that",
    "the", "this", "to", "was", "what", "when", "where", "which", "who",
    "with", "you", "your"
}


def meaningful_terms(text):
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {
        word for word in words
        if len(word) >= 4 and word not in STOPWORDS
    }


def check_grounding(answer, retrieved_chunks):
    context = " ".join(chunk["text"] for chunk in retrieved_chunks)
    grounding_terms = (
        meaningful_terms(answer) & meaningful_terms(context)
    )
    return len(grounding_terms) >= 2


def check_relevance(answer, question):
    question_terms = meaningful_terms(question)
    answer_terms = meaningful_terms(answer)
    overlap = question_terms & answer_terms
    return len(overlap) >= 2


def run_question(item):
    question = item["question"]

    response = requests.post(
        BASE_URL,
        json={"question": question, "top_k": 3},
        timeout=180,
    )

    result = {
        "id": item["id"],
        "category": item["category"],
        "question": question,
        "expected_context_available": item["expected_source"] is not None,
        "http_status": response.status_code,
    }

    if item["expected_source"] is None:
        passed = (
            response.status_code == 422
            and REFUSAL_TEXT in response.text
        )

        result.update({
            "test_type": "insufficient_context_refusal",
            "passed": passed,
            "reason": (
                "Expected controlled refusal because the knowledge base "
                "does not contain the requested information."
            ),
        })
        return result

    if response.status_code != 200:
        result.update({
            "test_type": "supported_output",
            "passed": False,
            "reason": f"Expected HTTP 200, got {response.status_code}.",
        })
        return result

    data = response.json()
    answer = data.get("answer", "").strip()
    chunks = data.get("retrieved_chunks", [])

    non_empty = bool(answer)
    grounding = check_grounding(answer, chunks)
    relevance = check_relevance(answer, question)
    format_valid = (
        bool(data.get("question"))
        and isinstance(data.get("retrieved_chunks"), list)
        and isinstance(data.get("orchestration_trace"), list)
        and "total_elapsed_ms" in data
    )

    passed = non_empty and grounding and relevance and format_valid

    result.update({
        "test_type": "supported_output",
        "passed": passed,
        "non_empty_answer": non_empty,
        "grounded_in_context": grounding,
        "relevant_to_question": relevance,
        "format_valid": format_valid,
        "top_similarity": (
            max(chunk["similarity_score"] for chunk in chunks)
            if chunks else None
        ),
    })

    return result


def main():
    with open(DATASET_PATH, "r", encoding="utf-8") as file:
        dataset = json.load(file)

    results = []

    for item in dataset:
        print(f"Testing {item['id']}: {item['question']}")
        result = run_question(item)
        results.append(result)
        print("  PASS" if result["passed"] else "  FAIL")

    total = len(results)
    passed = sum(result["passed"] for result in results)

    output = {
        "test_suite": "AI Output Testing and Guardrail Evaluation",
        "total_tests": total,
        "passed": passed,
        "failed": total - passed,
        "pass_rate_percent": round((passed / total) * 100, 2),
        "tests": results,
    }

    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(RESULTS_PATH, "w", encoding="utf-8") as file:
        json.dump(output, file, indent=2)

    print()
    print(f"Total: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    print(f"Pass rate: {output['pass_rate_percent']}%")
    print(f"Results saved to: {RESULTS_PATH}")


if __name__ == "__main__":
    main()
