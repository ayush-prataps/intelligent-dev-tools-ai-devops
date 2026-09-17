import json
import statistics
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
RESULTS_DIR = BASE_DIR / "results"

MODEL_FILES = {
    "codellama:7b-instruct": "codellama_7b-instruct_results.json",
    "phi3:mini": "phi3_mini_results.json",
    "qwen2.5:3b": "qwen2.5_3b_results.json",
}

# Manual evaluation labels.
# Correctness: 0 = incorrect, 1 = partially correct, 2 = fully correct.
CORRECTNESS = {
    "codellama:7b-instruct": [
        2, 2, 2, 2, 2, 2, 2, 0, 2, 2,
        1, 2, 2, 1, 2, 2, 2, 1, 2, 1,
    ],
    "phi3:mini": [
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    ],
    "qwen2.5:3b": [
        2, 2, 2, 2, 2, 1, 2, 2, 1, 2,
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    ],
}

# Relevance: 0 = irrelevant, 1 = partially relevant, 2 = highly relevant.
RELEVANCE = {
    "codellama:7b-instruct": [
        2, 2, 2, 1, 1, 1, 2, 1, 1, 2,
        1, 1, 1, 2, 2, 2, 2, 1, 2, 1,
    ],
    "phi3:mini": [
        2, 2, 1, 2, 2, 2, 2, 2, 2, 2,
        2, 2, 1, 2, 2, 2, 2, 2, 1, 2,
    ],
    "qwen2.5:3b": [
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
        2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
    ],
}

# Hallucination: 1 = at least one unsupported factual claim, 0 = no unsupported claim.
HALLUCINATION = {
    "codellama:7b-instruct": [
        0, 0, 0, 0, 1, 1, 0, 1, 0, 0,
        1, 1, 0, 1, 0, 0, 0, 1, 0, 1,
    ],
    "phi3:mini": [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 1, 0,
    ],
    "qwen2.5:3b": [
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0, 0, 0, 1, 0,
    ],
}


def load_results(filename):
    with open(RESULTS_DIR / filename, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_retrieval_quality(records):
    relevant = 0

    for record in records:
        expected_source = record.get("expected_source")
        expected_section = record.get("expected_section")

        if not expected_source or not expected_section:
            continue

        found = any(
            chunk["doc_id"] == Path(expected_source).stem
            and chunk["section"] == expected_section
            for chunk in record["retrieved_chunks"]
        )

        if found:
            relevant += 1

    valid_records = sum(
        1
        for record in records
        if record.get("expected_source")
        and record.get("expected_section")
    )

    return (
        relevant,
        valid_records,
        (relevant / valid_records) * 100 if valid_records else 0
    )


def calculate_performance(records):
    latencies = [record["llm_latency_ms"] for record in records]

    output_tokens = [
        record["eval_count"]
        for record in records
        if record.get("eval_count") is not None
    ]

    input_tokens = [
        record["prompt_eval_count"]
        for record in records
        if record.get("prompt_eval_count") is not None
    ]

    total_tokens = [
        record["prompt_eval_count"] + record["eval_count"]
        for record in records
        if record.get("prompt_eval_count") is not None
        and record.get("eval_count") is not None
    ]

    return {
        "latency_ms": {
            "average": round(statistics.mean(latencies), 2),
            "median": round(statistics.median(latencies), 2),
            "minimum": round(min(latencies), 2),
            "maximum": round(max(latencies), 2),
        },
        "tokens": {
            "average_input": round(statistics.mean(input_tokens), 2),
            "average_output": round(statistics.mean(output_tokens), 2),
            "average_total": round(statistics.mean(total_tokens), 2),
            "total": sum(total_tokens),
        },
    }


def score_model(model, records):
    correctness_scores = CORRECTNESS[model]
    relevance_scores = RELEVANCE[model]
    hallucination_labels = HALLUCINATION[model]

    if len(records) != 20:
        raise ValueError(
            f"{model}: expected 20 records, found {len(records)}"
        )

    if not (
        len(correctness_scores)
        == len(relevance_scores)
        == len(hallucination_labels)
        == len(records)
        == 20
    ):
        raise ValueError(f"{model}: scoring labels do not match 20 questions")

    correctness_total = sum(correctness_scores)
    relevance_total = sum(relevance_scores)
    hallucinated_responses = sum(hallucination_labels)

    retrieval_relevant, retrieval_total, retrieval_rate = (
        calculate_retrieval_quality(records)
    )

    performance = calculate_performance(records)

    return {
        "model": model,
        "questions": len(records),
        "quality": {
            "correctness": {
                "score": correctness_total,
                "maximum": 40,
                "percentage": round((correctness_total / 40) * 100, 2),
            },
            "relevance": {
                "score": relevance_total,
                "maximum": 40,
                "percentage": round((relevance_total / 40) * 100, 2),
            },
            "retrieval_quality": {
                "relevant_questions": retrieval_relevant,
                "total_questions": retrieval_total,
                "percentage": round(retrieval_rate, 2),
            },
            "hallucination_rate": {
                "hallucinated_responses": hallucinated_responses,
                "total_responses": 20,
                "percentage": round(
                    (hallucinated_responses / 20) * 100, 2
                ),
            },
        },
        "performance": performance,
    }


def main():
    results = []

    for model, filename in MODEL_FILES.items():
        records = load_results(filename)
        results.append(score_model(model, records))

    output_path = RESULTS_DIR / "evaluation_metrics.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "evaluation_methodology": {
                    "questions": 20,
                    "correctness_scale": "0-2",
                    "relevance_scale": "0-2",
                    "retrieval_quality": (
                        "1 if expected source and section are retrieved"
                    ),
                    "hallucination": (
                        "1 if response contains an unsupported factual claim"
                    ),
                    "latency": "llm_latency_ms",
                    "token_usage": (
                        "prompt_eval_count + eval_count"
                    ),
                },
                "models": results,
            },
            f,
            indent=2,
        )

    print(f"Saved metrics to {output_path}")
    print()

    for result in results:
        quality = result["quality"]
        performance = result["performance"]

        print(result["model"])
        print(
            f"  Correctness:       "
            f"{quality['correctness']['percentage']:.2f}%"
        )
        print(
            f"  Relevance:         "
            f"{quality['relevance']['percentage']:.2f}%"
        )
        print(
            f"  Retrieval Quality: "
            f"{quality['retrieval_quality']['percentage']:.2f}%"
        )
        print(
            f"  Hallucination:     "
            f"{quality['hallucination_rate']['percentage']:.2f}%"
        )
        print(
            f"  Avg Latency:       "
            f"{performance['latency_ms']['average']:.2f} ms"
        )
        print(
            f"  Median Latency:    "
            f"{performance['latency_ms']['median']:.2f} ms"
        )
        print(
            f"  Avg Total Tokens:  "
            f"{performance['tokens']['average_total']:.2f}"
        )
        print()


if __name__ == "__main__":
    main()
