"""Automated Verification Suite for Exercise 3: RAG Pipeline and Comparison."""
import math
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.retrieval_service import cosine_similarity, retrieve_top_k
from app.services.rag_service import build_augmented_prompt, run_rag_pipeline, run_comparison

client = TestClient(app)


def test_cosine_similarity_math():
    """Verify pure-Python cosine similarity handles identical, orthogonal, and opposing vectors."""
    # 1. Identical vectors -> 1.0
    v1 = [1.0, 2.0, 3.0]
    v2 = [1.0, 2.0, 3.0]
    assert math.isclose(cosine_similarity(v1, v2), 1.0, rel_tol=1e-5), "Identical vectors should yield 1.0"

    # 2. Orthogonal vectors -> 0.0
    v_orth1 = [1.0, 0.0]
    v_orth2 = [0.0, 1.0]
    assert math.isclose(cosine_similarity(v_orth1, v_orth2), 0.0, abs_tol=1e-5), "Orthogonal vectors should yield 0.0"

    # 3. Opposing vectors -> -1.0
    v_opp1 = [1.0, 1.0]
    v_opp2 = [-1.0, -1.0]
    assert math.isclose(cosine_similarity(v_opp1, v_opp2), -1.0, rel_tol=1e-5), "Opposing vectors should yield -1.0"

    # 4. Zero vector handling -> 0.0
    assert cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0, "Zero vectors must return 0.0 without divide-by-zero"

    # 5. Length mismatch -> 0.0
    assert cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0]) == 0.0, "Vector length mismatch must return 0.0"
    print("PASS: test_cosine_similarity_math")


def test_retrieval_ranking_and_top_k():
    """Verify retrieve_top_k ranks chunks descending by similarity and respects top_k count."""
    mock_chunks = [
        {"chunk_id": "c1", "doc_id": "d1", "doc_title": "Doc 1", "section": "Sec 1", "embedding": [0.1, 0.9], "text": "Low match"},
        {"chunk_id": "c2", "doc_id": "d2", "doc_title": "Doc 2", "section": "Sec 2", "embedding": [0.9, 0.1], "text": "High match"},
        {"chunk_id": "c3", "doc_id": "d3", "doc_title": "Doc 3", "section": "Sec 3", "embedding": [0.5, 0.5], "text": "Medium match"},
    ]

    with patch("app.services.retrieval_service.load_knowledge_base", return_value={"chunks": mock_chunks}):
        # Query aligned with c2 [0.9, 0.1]
        query_vec = [1.0, 0.0]
        results = retrieve_top_k(query_vec, top_k=2)

        assert len(results) == 2, f"Expected 2 chunks, got {len(results)}"
        assert results[0]["chunk_id"] == "c2", f"Top ranked chunk should be c2, got {results[0]['chunk_id']}"
        assert results[1]["chunk_id"] == "c3", f"Second ranked chunk should be c3, got {results[1]['chunk_id']}"
        assert results[0]["similarity_score"] >= results[1]["similarity_score"], "Results must be sorted descending"

        # Verify required fields are present
        for field in ["chunk_id", "doc_title", "section", "similarity_score", "text"]:
            assert field in results[0], f"Field '{field}' missing from retrieved chunk"
    print("PASS: test_retrieval_ranking_and_top_k")


def test_prompt_construction():
    """Verify augmented prompt includes question, section titles, and chunk texts."""
    sample_chunks = [
        {
            "doc_title": "University Attendance Policy",
            "section": "Minimum Attendance Requirement",
            "text": "Students must maintain 75% attendance."
        }
    ]
    prompt = build_augmented_prompt("What is the attendance rule?", sample_chunks)
    assert "University Attendance Policy" in prompt
    assert "Minimum Attendance Requirement" in prompt
    assert "Students must maintain 75% attendance." in prompt
    assert "What is the attendance rule?" in prompt
    assert "Grounded Answer:" in prompt
    print("PASS: test_prompt_construction")


def test_rag_endpoint():
    """Verify POST /api/rag returns grounded answer and retrieved chunks."""
    mock_chunks = [
        {"chunk_id": "c1", "doc_id": "attendance", "doc_title": "Attendance Policy", "section": "Min Attendance", "embedding": [0.5] * 768, "text": "75% required"}
    ]

    async def mock_get_embedding(text: str):
        return [0.5] * 768

    async def mock_generate_answer(prompt: str):
        return "Based on the policy, students must maintain 75% attendance."

    with patch("app.services.rag_service.get_embedding", side_effect=mock_get_embedding), \
         patch("app.services.rag_service.generate_answer", side_effect=mock_generate_answer), \
         patch("app.services.retrieval_service.load_knowledge_base", return_value={"chunks": mock_chunks}):

        response = client.post("/api/rag", json={"question": "What is the attendance rule?", "top_k": 1})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "answer" in data
        assert "75% required" in data["retrieved_chunks"][0]["text"]
        assert len(data["retrieved_chunks"]) == 1
    print("PASS: test_rag_endpoint")


def test_comparison_endpoint():
    """Verify POST /api/compare returns both direct and RAG answers alongside retrieved chunks."""
    mock_chunks = [
        {"chunk_id": "c1", "doc_id": "exam", "doc_title": "Exam Rules", "section": "Entry", "embedding": [0.5] * 768, "text": "ID card required"}
    ]

    async def mock_get_embedding(text: str):
        return [0.5] * 768

    async def mock_generate_answer(prompt: str):
        if "Retrieved Context" in prompt:
            return "RAG Answer: Physical ID card is mandatory."
        return "Direct Answer: Bring your student ID or digital card."

    with patch("app.services.rag_service.get_embedding", side_effect=mock_get_embedding), \
         patch("app.services.rag_service.generate_answer", side_effect=mock_generate_answer), \
         patch("app.services.retrieval_service.load_knowledge_base", return_value={"chunks": mock_chunks}):

        response = client.post("/api/compare", json={"question": "What ID is allowed in the exam?", "top_k": 1})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "direct_answer" in data
        assert "rag_answer" in data
        assert "retrieved_chunks" in data
        assert "Direct Answer" in data["direct_answer"]
        assert "RAG Answer" in data["rag_answer"]
        assert len(data["retrieved_chunks"]) == 1
    print("PASS: test_comparison_endpoint")


if __name__ == "__main__":
    test_cosine_similarity_math()
    test_retrieval_ranking_and_top_k()
    test_prompt_construction()
    test_rag_endpoint()
    test_comparison_endpoint()
    print("\nALL EXERCISE 3 AUTOMATED TESTS PASSED SUCCESSFULLY!")
