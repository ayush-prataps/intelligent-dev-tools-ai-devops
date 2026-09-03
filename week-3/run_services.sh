#!/bin/bash
# ==============================================================================
# Script to launch all 3 microservices for Week 3 Exercise 4:
# 1. Retrieval Service (Port 8001)
# 2. LLM Service (Port 8002)
# 3. Application / Orchestrator Service (Port 8000)
# ==============================================================================

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

# Choose Python binary
if [ -d "venv" ]; then
    PYTHON="$DIR/venv/bin/python"
    UVICORN="$DIR/venv/bin/uvicorn"
else
    PYTHON="python3"
    UVICORN="uvicorn"
fi

echo "============================================================"
echo " Starting University Knowledge Assistant Microservices"
echo "============================================================"

# Ensure child processes terminate on script exit
cleanup() {
    echo ""
    echo "Stopping all microservices..."
    kill $PID_RETRIEVAL 2>/dev/null || true
    kill $PID_LLM 2>/dev/null || true
    kill $PID_APP 2>/dev/null || true
    wait $PID_RETRIEVAL 2>/dev/null || true
    wait $PID_LLM 2>/dev/null || true
    wait $PID_APP 2>/dev/null || true
    echo "All microservices stopped cleanly."
}
trap cleanup EXIT INT TERM

# 1. Start Retrieval Service on port 8001
echo "--> Starting Retrieval Service on http://127.0.0.1:8001..."
PYTHONPATH="$DIR" $UVICORN services.retrieval_service.main:app --port 8001 --host 0.0.0.0 &
PID_RETRIEVAL=$!

# 2. Start LLM Service on port 8002
echo "--> Starting LLM Service on http://127.0.0.1:8002..."
PYTHONPATH="$DIR" $UVICORN services.llm_service.main:app --port 8002 --host 0.0.0.0 &
PID_LLM=$!

# Allow microservices a moment to initialize
sleep 1.5

# 3. Start Application / Orchestrator Service on port 8000
echo "--> Starting Application / Orchestrator Service on http://127.0.0.1:8000..."
PYTHONPATH="$DIR" $UVICORN app.main:app --port 8000 --host 0.0.0.0 &
PID_APP=$!

echo "============================================================"
echo " All services running:"
echo " - Application Service: http://localhost:8000"
echo " - Retrieval Service:   http://localhost:8001"
echo " - LLM Service:         http://localhost:8002"
echo " Press Ctrl+C to terminate all services."
echo "============================================================"

# Wait on all processes
wait
