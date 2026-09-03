"""Automated Verification Suite for Exercise 1: University Knowledge Assistant."""
import asyncio
from unittest.mock import patch
import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_minimal():
    """Verify /api/health returns only {'status': 'ok'} without sensitive details."""
    response = client.get("/api/health")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert response.json() == {"status": "ok"}, f"Expected {{'status': 'ok'}}, got {response.json()}"
    print("PASS: test_health_check_minimal")


def test_static_files_served():
    """Verify root / serves the frontend index.html."""
    response = client.get("/")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    assert "University Knowledge Assistant" in response.text, "Title not found in HTML"
    assert "Ask Assistant" in response.text, "Submit button not found in HTML"
    assert "style.css" in response.text, "Stylesheet link not found in HTML"
    assert "app.js" in response.text, "Script tag not found in HTML"
    print("PASS: test_static_files_served")


def test_ask_schema_validation():
    """Verify /api/ask rejects invalid/empty payload with HTTP 422."""
    # Empty JSON
    response = client.post("/api/ask", json={})
    assert response.status_code == 422, f"Expected 422 for empty payload, got {response.status_code}"

    # Invalid type
    response = client.post("/api/ask", json={"question": 12345})
    assert response.status_code == 422, f"Expected 422 for numeric question, got {response.status_code}"
    print("PASS: test_ask_schema_validation")


def test_ask_ollama_unreachable_error():
    """Verify /api/ask returns HTTP 503 with clear message when Ollama is unreachable."""
    with patch("app.services.ollama_service.OLLAMA_BASE_URL", "http://127.0.0.1:9999"):
        response = client.post("/api/ask", json={"question": "What is an operating system?"})
        assert response.status_code == 503, f"Expected 503 when Ollama is offline, got {response.status_code}"
        data = response.json()
        assert "Cannot connect to Ollama" in data.get("detail", ""), f"Unexpected error detail: {data}"
    print("PASS: test_ask_ollama_unreachable_error")


def test_ask_successful_response():
    """Verify /api/ask parses and returns model answer when Ollama responds."""
    mock_ollama_response = {
        "model": "codellama:7b-instruct",
        "created_at": "2026-09-03T06:50:00Z",
        "response": "In computer science, a process is an instance of a computer program that is being executed.",
        "done": True
    }

    # Mock httpx.AsyncClient.post
    async def mock_post(*args, **kwargs):
        class MockResponse:
            status_code = 200
            def json(self):
                return mock_ollama_response
            @property
            def text(self):
                return ""
        return MockResponse()

    with patch("httpx.AsyncClient.post", side_effect=mock_post):
        response = client.post("/api/ask", json={"question": "What is a process?"})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "answer" in data, "Key 'answer' missing from response"
        assert data["answer"] == mock_ollama_response["response"]
    print("PASS: test_ask_successful_response")


if __name__ == "__main__":
    test_health_check_minimal()
    test_static_files_served()
    test_ask_schema_validation()
    test_ask_ollama_unreachable_error()
    test_ask_successful_response()
    print("\nALL 5 AUTOMATED VERIFICATION TESTS PASSED SUCCESSFULLY!")
