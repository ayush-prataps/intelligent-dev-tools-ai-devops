"""Automated Verification Suite for Exercise 4: Microservices & Orchestration."""
from unittest.mock import patch
from fastapi.testclient import TestClient

from services.retrieval_service.main import app as retrieval_app
from services.llm_service.main import app as llm_app
from app.main import app as app_gateway

client_retrieval = TestClient(retrieval_app)
client_llm = TestClient(llm_app)
client_gateway = TestClient(app_gateway)


# 1. Test Retrieval Service Endpoints
def test_retrieval_service_health():
    """Verify Retrieval Service exposes /health returning status ok and service identifier."""
    res = client_retrieval.get("/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "retrieval_service"
    print("PASS: test_retrieval_service_health")


def test_retrieval_service_retrieve_endpoint():
    """Verify Retrieval Service /retrieve computes similarity and returns ranked chunks."""
    async def mock_get_embedding(text: str):
        return [0.05] * 768

    with patch("services.retrieval_service.main.get_query_embedding", side_effect=mock_get_embedding):
        res = client_retrieval.post("/retrieve", json={"query": "attendance policy", "top_k": 2})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert "retrieved_chunks" in data
        assert len(data["retrieved_chunks"]) == 2
        first = data["retrieved_chunks"][0]
        assert "chunk_id" in first
        assert "doc_title" in first
        assert "similarity_score" in first
        assert "text" in first
    print("PASS: test_retrieval_service_retrieve_endpoint")


# 2. Test LLM Service Endpoints
def test_llm_service_health():
    """Verify LLM Service exposes /health returning status ok and service identifier."""
    res = client_llm.get("/health")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}"
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "llm_service"
    print("PASS: test_llm_service_health")


def test_llm_service_generate_endpoint():
    """Verify LLM Service /generate calls Ollama and returns completion."""
    mock_ollama_json = {
        "model": "codellama:7b-instruct",
        "response": "Undergraduate students must maintain 75% attendance.",
        "done": True
    }

    async def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return mock_ollama_json
            @property
            def text(self):
                return ""
        return MockResponse()

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        res = client_llm.post("/generate", json={"prompt": "What is attendance rule?"})
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert data["answer"] == mock_ollama_json["response"]
        assert data["model"] == "codellama:7b-instruct"
    print("PASS: test_llm_service_generate_endpoint")


# 3. Test Application Orchestrator Service
def test_orchestration_pipeline_and_trace():
    """Verify POST /api/orchestrate calls microservices over HTTP and produces an execution trace."""
    mock_retrieval_res = {
        "query": "attendance",
        "top_k": 2,
        "retrieved_chunks": [
            {
                "chunk_id": "c1",
                "doc_id": "attendance",
                "doc_title": "Attendance Policy",
                "section": "Min Attendance",
                "similarity_score": 0.85,
                "text": "75% required"
            }
        ]
    }
    mock_llm_res = {
        "answer": "Orchestrated grounded response: 75% attendance is required.",
        "model": "codellama:7b-instruct"
    }

    async def mock_client_post(self, url, **kwargs):
        class MockResponse:
            def __init__(self, data):
                self.status_code = 200
                self._data = data
                self.text = ""
            def json(self):
                return self._data

        if "/retrieve" in str(url):
            return MockResponse(mock_retrieval_res)
        elif "/generate" in str(url):
            return MockResponse(mock_llm_res)
        raise ValueError(f"Unexpected URL: {url}")

    with patch("httpx.AsyncClient.post", mock_client_post):
        res = client_gateway.post(
            "/api/orchestrate",
            json={"question": "What is the minimum attendance requirement?", "top_k": 2}
        )
        assert res.status_code == 200, f"Expected 200, got {res.status_code}"
        data = res.json()
        assert data["answer"] == mock_llm_res["answer"]
        assert len(data["retrieved_chunks"]) == 1
        assert "orchestration_trace" in data

        trace = data["orchestration_trace"]
        assert len(trace) >= 5, f"Expected at least 5 trace steps, got {len(trace)}"

        # Verify trace steps structure
        steps = [t["step"] for t in trace]
        assert steps == [1, 2, 3, 4, 5], f"Trace step numbers should be 1-5, got {steps}"

        services = [t["service"] for t in trace]
        assert "Application Service" in services
        assert "Retrieval Service" in services
        assert "LLM Service" in services

        for step in trace:
            assert "action" in step
            assert "status" in step
            assert "elapsed_ms" in step
            assert step["status"] == "completed"
            assert step["elapsed_ms"] >= 0.0

        assert "total_elapsed_ms" in data
        assert data["total_elapsed_ms"] >= 0.0
    print("PASS: test_orchestration_pipeline_and_trace")


if __name__ == "__main__":
    test_retrieval_service_health()
    test_retrieval_service_retrieve_endpoint()
    test_llm_service_health()
    test_llm_service_generate_endpoint()
    test_orchestration_pipeline_and_trace()
    print("\nALL EXERCISE 4 AUTOMATED TESTS PASSED SUCCESSFULLY!")
