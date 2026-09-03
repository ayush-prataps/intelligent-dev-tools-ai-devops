"""Automated Verification Suite for Exercise 2: Knowledge Base Stage."""
import os
import json
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.services.chunking_service import chunk_markdown_document
from app.services.knowledge_service import (
    get_raw_documents,
    build_knowledge_base,
    load_knowledge_base
)

client = TestClient(app)


def test_documents_exist_and_load():
    """Verify all 5 realistic university documents are present and non-empty."""
    docs = get_raw_documents()
    assert len(docs) == 5, f"Expected 5 documents, found {len(docs)}"
    
    expected_doc_ids = {
        "attendance_policy",
        "examination_rules",
        "academic_policies",
        "leave_policy",
        "campus_facilities"
    }
    actual_ids = {d["id"] for d in docs}
    assert expected_doc_ids == actual_ids, f"Mismatch in doc IDs: {actual_ids}"

    for d in docs:
        assert len(d["content"]) > 100, f"Document {d['id']} is too short or empty"
        assert d["title"] != "", f"Document {d['id']} missing title"
    print("PASS: test_documents_exist_and_load")


def test_semantic_chunking():
    """Verify semantic chunking parses sections and preserves hierarchical context."""
    sample_md = (
        "# Student Handbook\n\n"
        "## Grading Scale\n"
        "The grading scale ranges from O to F.\n\n"
        "## Conduct Rules\n"
        "Students must maintain decorum in all classrooms and labs."
    )
    chunks = chunk_markdown_document("handbook", sample_md)
    assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"

    # Check context preservation
    assert "[Student Handbook > Grading Scale]" in chunks[0]["text"]
    assert chunks[0]["section"] == "Grading Scale"
    assert chunks[0]["chunk_id"] == "handbook_chunk_01"

    assert "[Student Handbook > Conduct Rules]" in chunks[1]["text"]
    assert chunks[1]["section"] == "Conduct Rules"
    assert chunks[1]["chunk_id"] == "handbook_chunk_02"
    print("PASS: test_semantic_chunking")


def test_embedding_fails_loudly_when_offline():
    """Verify embedding service raises 503 when Ollama is offline instead of silent mock fallback."""
    with patch("app.services.embedding_service.OLLAMA_BASE_URL", "http://127.0.0.1:9999"):
        from app.services.embedding_service import get_embedding
        import asyncio
        from fastapi import HTTPException

        try:
            asyncio.run(get_embedding("Test prompt"))
            assert False, "Should have raised HTTPException"
        except HTTPException as exc:
            assert exc.status_code == 503
            assert "Cannot connect to Ollama" in exc.detail
    print("PASS: test_embedding_fails_loudly_when_offline")


def test_dynamic_dimension_detection_and_build():
    """Verify knowledge base determines dimension dynamically from vector response length."""
    # Simulate an embedding model that returns vectors of arbitrary length (e.g. 512 dimensions)
    custom_dim = 512
    mock_vector = [0.01 * (i % 10) for i in range(custom_dim)]

    async def mock_get_embedding(text: str):
        return list(mock_vector)

    with patch("app.services.knowledge_service.get_embedding", side_effect=mock_get_embedding):
        import asyncio
        kb = asyncio.run(build_knowledge_base())
        
        # Verify dimension was dynamically determined as 512 (not hardcoded 768)
        assert kb["metadata"]["embedding_dimension"] == custom_dim, (
            f"Expected dynamic dimension {custom_dim}, got {kb['metadata']['embedding_dimension']}"
        )
        assert kb["metadata"]["total_documents"] == 5
        assert kb["metadata"]["total_chunks"] > 0
        assert len(kb["chunks"][0]["embedding"]) == custom_dim
    print("PASS: test_dynamic_dimension_detection_and_build")


def test_knowledge_api_endpoints():
    """Verify GET endpoints for knowledge base summary, documents, and chunks."""
    # Summary
    res_summary = client.get("/api/knowledge/summary")
    assert res_summary.status_code == 200
    summary = res_summary.json()
    assert "total_documents" in summary
    assert "embedding_dimension" in summary

    # Documents list
    res_docs = client.get("/api/knowledge/documents")
    assert res_docs.status_code == 200
    docs = res_docs.json()
    assert len(docs) == 5

    # Chunks inspection
    res_chunks = client.get("/api/knowledge/chunks")
    assert res_chunks.status_code == 200
    chunks_data = res_chunks.json()
    assert "chunks" in chunks_data
    if chunks_data["chunks"]:
        first_chunk = chunks_data["chunks"][0]
        assert "vector_dimension" in first_chunk
        assert "vector_sample" in first_chunk
        assert "chunk_id" in first_chunk
    print("PASS: test_knowledge_api_endpoints")


if __name__ == "__main__":
    test_documents_exist_and_load()
    test_semantic_chunking()
    test_embedding_fails_loudly_when_offline()
    test_dynamic_dimension_detection_and_build()
    test_knowledge_api_endpoints()
    print("\nALL EXERCISE 2 AUTOMATED TESTS PASSED SUCCESSFULLY!")
