# Week 5 – Automated RAG Evaluation and Guardrail Comparison

## Implemented changes

The Week 5 branch adds an automated evaluation workflow without changing the existing RAG architecture:

- Reuses the existing embedding and cosine-similarity retrieval pipeline.
- Reuses the existing augmented prompt and Ollama generation service.
- Evaluates the Week 4 question dataset using the same retrieved context process.
- Supports multiple local models in one evaluation request.
- Records per-question latency, model metrics, similarity scores, and guardrail-trigger information.
- Aggregates correctness, relevance, grounding, retrieval-quality, latency, success, and guardrail-trigger counts per model.
- Captures process-level CPU time and maximum resident memory (RSS) through Python resource measurements.
- Adds a dataset evaluation endpoint:

```http
POST /api/rag/evaluate-dataset
```

Example request:

```json
{
  "models": ["phi3:mini", "qwen2.5:3b"],
  "limit": 2
}
```

## Metric interpretation

The automated correctness, relevance, and grounding values are heuristic lexical-overlap indicators. They are useful for repeatable screening and comparison, but they do not replace human evaluation or the Week 4 manually scored rubric.

Retrieval quality is estimated from the highest retrieved similarity relative to the configured guardrail threshold of `0.65`. Questions reaching the threshold receive a score of `1.0`; lower scores are normalized against the threshold.

The guardrail comparison endpoint continues to report both the guarded decision and the unguarded generation output so that unsupported-context behavior can be inspected experimentally.

## Limitations

- CPU and RSS measurements are process-level measurements and should be interpreted as approximate runtime indicators.
- The evaluation service uses lexical overlap rather than an external judge model.
- The full 20-question run can take substantial time on a CPU-only VM.
- The unguarded response in guardrail comparison is intentionally generated for evaluation and should not be used as the production response when retrieval validation fails.
