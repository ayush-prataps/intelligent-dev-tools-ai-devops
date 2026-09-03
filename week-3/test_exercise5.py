"""Automated Verification Suite for Exercise 5: Docker Containerization & Compose Orchestration.

Tests are divided into two distinct categories:
  CATEGORY A — STATIC TESTS: Validates Dockerfile & docker-compose.yml specifications offline (Runs on Mac/CI).
  CATEGORY B — LIVE DOCKER TESTS: Validates live running Docker containers over HTTP (Runs on Ubuntu VM).
"""
import os
import sys
import yaml
import httpx

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCKERFILE_PATH = os.path.join(BASE_DIR, "Dockerfile")
COMPOSE_PATH = os.path.join(BASE_DIR, "docker-compose.yml")


# ==============================================================================
# CATEGORY A: STATIC CONFIGURATION TESTS (Mac / Offline Friendly)
# ==============================================================================

def test_static_dockerfile_specification():
    """Verify Dockerfile exists, uses python:3.12-slim, and copies required directories."""
    assert os.path.isfile(DOCKERFILE_PATH), f"Dockerfile missing at: {DOCKERFILE_PATH}"

    with open(DOCKERFILE_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Base image
    assert "python:3.12-slim" in content, "Dockerfile must use python:3.12-slim base image"

    # 2. Dependency installation
    assert "requirements.txt" in content, "Dockerfile must install requirements.txt"
    assert "pip install" in content, "Dockerfile must run pip install"

    # 3. Required application directories copied
    assert "COPY app/" in content or "COPY app" in content, "Dockerfile must copy app/"
    assert "COPY services/" in content or "COPY services" in content, "Dockerfile must copy services/"
    assert "data/" in content, "Dockerfile must include data/"

    print("  PASS: test_static_dockerfile_specification")


def test_static_compose_services_and_ports():
    """Verify docker-compose.yml defines exactly the 3 microservices and their port mappings."""
    assert os.path.isfile(COMPOSE_PATH), f"docker-compose.yml missing at: {COMPOSE_PATH}"

    with open(COMPOSE_PATH, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data.get("services", {})

    # 1. Exactly 3 services defined
    expected_services = {"application", "retrieval", "llm"}
    actual_services = set(services.keys())
    assert actual_services == expected_services, (
        f"Expected exactly services {expected_services}, found {actual_services}"
    )

    # 2. Ollama must NOT be containerized in Docker Compose (runs on VM directly)
    assert "ollama" not in services, (
        "Ollama must NOT be a container service. It runs natively on the VM."
    )

    # 3. Port mappings verification
    app_ports = [str(p) for p in services["application"].get("ports", [])]
    assert any("8000:8000" in p for p in app_ports), "Application must map port 8000:8000"

    retrieval_ports = [str(p) for p in services["retrieval"].get("ports", [])]
    assert any("8001:8001" in p for p in retrieval_ports), "Retrieval must map port 8001:8001"

    llm_ports = [str(p) for p in services["llm"].get("ports", [])]
    assert any("8002:8002" in p for p in llm_ports), "LLM must map port 8002:8002"

    print("  PASS: test_static_compose_services_and_ports")


def test_static_compose_networking_and_env():
    """Verify internal Compose DNS names, host-gateway for VM Ollama, and required environment vars."""
    with open(COMPOSE_PATH, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)

    services = compose_data["services"]

    # 1. Application service environment & networking
    app_env = dict(
        item.split("=", 1) if isinstance(item, str) else item
        for item in (services["application"].get("environment") or [])
    )
    assert app_env.get("RETRIEVAL_SERVICE_URL") == "http://retrieval:8001", (
        "Application must use http://retrieval:8001 (internal Docker DNS)"
    )
    assert app_env.get("LLM_SERVICE_URL") == "http://llm:8002", (
        "Application must use http://llm:8002 (internal Docker DNS)"
    )
    assert "SERVICE_TIMEOUT_SECONDS" in app_env, "Application must specify SERVICE_TIMEOUT_SECONDS"

    # 2. Retrieval service environment & host-gateway
    retrieval_env = dict(
        item.split("=", 1) if isinstance(item, str) else item
        for item in (services["retrieval"].get("environment") or [])
    )
    assert retrieval_env.get("OLLAMA_BASE_URL") == "http://host.docker.internal:11434", (
        "Retrieval must target http://host.docker.internal:11434"
    )
    assert retrieval_env.get("EMBEDDING_MODEL") == "nomic-embed-text", (
        "Retrieval must use nomic-embed-text"
    )
    retrieval_hosts = services["retrieval"].get("extra_hosts", [])
    assert "host.docker.internal:host-gateway" in retrieval_hosts, (
        "Retrieval must configure extra_hosts: host.docker.internal:host-gateway"
    )

    # 3. LLM service environment & host-gateway
    llm_env = dict(
        item.split("=", 1) if isinstance(item, str) else item
        for item in (services["llm"].get("environment") or [])
    )
    assert llm_env.get("OLLAMA_BASE_URL") == "http://host.docker.internal:11434", (
        "LLM must target http://host.docker.internal:11434"
    )
    assert llm_env.get("OLLAMA_MODEL") == "codellama:7b-instruct" or llm_env.get("MODEL_NAME") == "codellama:7b-instruct", (
        "LLM must specify codellama:7b-instruct"
    )
    llm_hosts = services["llm"].get("extra_hosts", [])
    assert "host.docker.internal:host-gateway" in llm_hosts, (
        "LLM must configure extra_hosts: host.docker.internal:host-gateway"
    )

    print("  PASS: test_static_compose_networking_and_env")


# ==============================================================================
# CATEGORY B: LIVE DOCKER TESTS (Ubuntu VM with Docker Compose)
# ==============================================================================

def check_live_docker_availability() -> bool:
    """Check if all three Docker services are reachable on localhost."""
    try:
        r_app = httpx.get("http://127.0.0.1:8000/api/health", timeout=1.5)
        r_ret = httpx.get("http://127.0.0.1:8001/health", timeout=1.5)
        r_llm = httpx.get("http://127.0.0.1:8002/health", timeout=1.5)
        return r_app.status_code == 200 and r_ret.status_code == 200 and r_llm.status_code == 200
    except Exception:
        return False


def test_live_docker_health_endpoints():
    """Verify live Docker containers on ports 8000, 8001, and 8002 respond to health checks."""
    res_app = httpx.get("http://127.0.0.1:8000/api/health", timeout=5.0)
    assert res_app.status_code == 200, f"Application returned status {res_app.status_code}"
    assert res_app.json().get("status") == "ok"

    res_ret = httpx.get("http://127.0.0.1:8001/health", timeout=5.0)
    assert res_ret.status_code == 200, f"Retrieval service returned status {res_ret.status_code}"
    assert res_ret.json().get("service") == "retrieval_service"

    res_llm = httpx.get("http://127.0.0.1:8002/health", timeout=5.0)
    assert res_llm.status_code == 200, f"LLM service returned status {res_llm.status_code}"
    assert res_llm.json().get("service") == "llm_service"

    print("  PASS: test_live_docker_health_endpoints")


def test_live_docker_orchestration_workflow():
    """Verify live containerized orchestration workflow, retrieved chunks, and trace steps."""
    payload = {
        "question": "What is the minimum attendance requirement and can it be condoned?",
        "top_k": 2
    }
    # CPU inference with 7B model can take 30-90s on a VM
    res = httpx.post(
        "http://127.0.0.1:8000/api/orchestrate",
        json=payload,
        timeout=180.0
    )
    assert res.status_code == 200, f"Orchestrate failed with status {res.status_code}: {res.text}"

    data = res.json()

    # 1. Non-empty answer
    assert data.get("answer") and len(data["answer"].strip()) > 0, "Expected non-empty generated answer"

    # 2. Retrieved chunks present with valid fields (no hardcoded similarity score)
    chunks = data.get("retrieved_chunks", [])
    assert len(chunks) >= 1, "Expected at least 1 retrieved chunk"
    for c in chunks:
        assert c.get("chunk_id"), "Chunk missing chunk_id"
        assert c.get("doc_title"), "Chunk missing doc_title"
        assert c.get("section"), "Chunk missing section"
        assert c.get("text"), "Chunk missing text"
        assert isinstance(c.get("similarity_score"), (int, float)), "Chunk missing numerical similarity score"

    # 3. Orchestration trace contains exactly 5 completed steps with non-negative timings
    trace = data.get("orchestration_trace", [])
    assert len(trace) == 5, f"Expected exactly 5 trace steps, got {len(trace)}"

    for step in trace:
        assert step.get("status") == "completed", f"Step {step.get('step')} status was not 'completed'"
        assert "service" in step, "Trace step missing service name"
        assert "action" in step, "Trace step missing action description"
        assert step.get("elapsed_ms", -1) >= 0.0, "Elapsed ms must be non-negative"

    assert data.get("total_elapsed_ms", -1) >= 0.0, "Total elapsed ms must be non-negative"

    print("  PASS: test_live_docker_orchestration_workflow")


# ==============================================================================
# MAIN TEST RUNNER
# ==============================================================================

if __name__ == "__main__":
    print("\n============================================================")
    print(" WEEK 3 EXERCISE 5: DOCKER CONTAINERIZATION TEST SUITE")
    print("============================================================")

    print("\n--- CATEGORY A: STATIC CONFIGURATION TESTS (Mac / Offline) ---")
    test_static_dockerfile_specification()
    test_static_compose_services_and_ports()
    test_static_compose_networking_and_env()
    print("RESULT: Category A Static Tests: 3/3 PASS")

    print("\n--- CATEGORY B: LIVE DOCKER TESTS (Ubuntu VM / Compose Up) ---")
    if check_live_docker_availability():
        print("Live Docker services detected on localhost. Running live tests...")
        test_live_docker_health_endpoints()
        test_live_docker_orchestration_workflow()
        print("RESULT: Category B Live Docker Tests: 2/2 PASS")
    else:
        print("SKIPPED: Live Docker services are not running on localhost (Ports 8000, 8001, 8002 unreachable).")
        print("         This is expected on Mac / Antigravity development environment.")
        print("         Run this suite on the Ubuntu VM after: docker compose up -d")

    print("\n============================================================")
    print(" Exercise 5 test execution completed.")
    print("============================================================\n")
