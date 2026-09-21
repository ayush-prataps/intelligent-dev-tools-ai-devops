"""Guardrails for the University Knowledge Assistant."""

import re


MAX_QUESTION_LENGTH = 500
MIN_RETRIEVAL_SIMILARITY = 0.65
MIN_GROUNDING_TERMS = 2

GUARDRAIL_REFUSAL = (
    "I'm unable to answer this question from the available university "
    "knowledge base. Please ask a question related to university policies "
    "or information covered by the system."
)

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "have", "how", "in", "is", "it", "of", "on", "or", "that",
    "the", "this", "to", "was", "what", "when", "where", "which", "who",
    "with", "you", "your"
}


def validate_input(question: str) -> tuple[bool, str]:
    """Validate basic input constraints before retrieval."""
    if not question or not question.strip():
        return False, "Please provide a question."

    if len(question.strip()) > MAX_QUESTION_LENGTH:
        return False, (
            f"Question exceeds the maximum allowed length of "
            f"{MAX_QUESTION_LENGTH} characters."
        )

    return True, ""


def validate_retrieval(retrieved_chunks) -> tuple[bool, str]:
    """Require sufficient retrieval evidence before calling the LLM."""
    if not retrieved_chunks:
        return False, GUARDRAIL_REFUSAL

    top_score = max(chunk.similarity_score for chunk in retrieved_chunks)

    if top_score < MIN_RETRIEVAL_SIMILARITY:
        return False, GUARDRAIL_REFUSAL

    return True, ""


def _meaningful_terms(text: str) -> set[str]:
    """Extract simple content terms for the grounding heuristic."""
    words = re.findall(r"[a-zA-Z0-9]+", text.lower())
    return {
        word
        for word in words
        if len(word) >= 4 and word not in STOPWORDS
    }


def validate_output(answer: str, retrieved_chunks) -> tuple[bool, str]:
    """Reject empty or weakly grounded LLM output."""
    if not answer or not answer.strip():
        return False, GUARDRAIL_REFUSAL

    context_text = " ".join(chunk.text for chunk in retrieved_chunks)

    context_terms = _meaningful_terms(context_text)
    answer_terms = _meaningful_terms(answer)

    grounding_terms = context_terms.intersection(answer_terms)

    required_terms = min(MIN_GROUNDING_TERMS, len(context_terms))
    if len(grounding_terms) < required_terms:
        return False, GUARDRAIL_REFUSAL

    return True, ""
