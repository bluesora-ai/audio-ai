#!/bin/bash
# Test script for deployment verification
set -e

echo "=== Testing Audio Provenance System Deployment ==="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Activate venv
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo -e "${RED}Error: Virtual environment not found!${NC}"
    exit 1
fi

# Test counter
PASSED=0
FAILED=0

# Function to run test
test_command() {
    local name=$1
    local command=$2
    
    echo -n "Testing $name... "
    if eval "$command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((FAILED++))
        return 1
    fi
}

echo "=== Python Environment Tests ==="
test_command "Python version" "python3 --version | grep -q 'Python 3.10'"
test_command "Virtual environment" "[ -d venv ]"
test_command "PyTorch" "python3 -c 'import torch'"
test_command "FAISS" "python3 -c 'import faiss'"
test_command "FastAPI" "python3 -c 'import fastapi'"
test_command "Demucs" "python3 -c 'import demucs' 2>/dev/null || echo 'Optional: Demucs not installed'"

echo ""
echo "=== Module Import Tests ==="
test_command "Pipeline Orchestrator" "python3 -c 'from src.pipeline import PipelineOrchestrator'"
test_command "Stem Separator" "python3 -c 'from src.stage2_preprocessing import StemSeparator'"
test_command "Embedding Generator" "python3 -c 'from src.stage3_embedding import EmbeddingGenerator'"
test_command "FAISS Indexer" "python3 -c 'from src.stage4_indexing import FAISSIndexer'"
test_command "AI Detector" "python3 -c 'from src.stage5_classifier import AIDetector'"
test_command "Report Builder" "python3 -c 'from src.stage6_reporting import ProvenanceReportBuilder'"

echo ""
echo "=== Directory Structure Tests ==="
test_command "Data directories" "[ -d data/raw ] && [ -d data/embeddings ] && [ -d data/indexes ]"
test_command "Models directory" "[ -d models ]"
test_command "Scripts directory" "[ -d scripts ]"

echo ""
echo "=== File Existence Tests ==="
test_command "API main" "[ -f api/main.py ]"
test_command "Requirements" "[ -f requirements.txt ]"
test_command "Config settings" "[ -f config/settings.py ]"

echo ""
echo "=== API Server Test ==="
echo "Starting API server test..."
# Start server in background
uvicorn api.main:app --host 127.0.0.1 --port 8001 > /tmp/api_test.log 2>&1 &
API_PID=$!
sleep 3

# Test health endpoint
if curl -s http://127.0.0.1:8001/health | grep -q "healthy"; then
    echo -e "API Health Check: ${GREEN}✓ PASSED${NC}"
    ((PASSED++))
else
    echo -e "API Health Check: ${RED}✗ FAILED${NC}"
    ((FAILED++))
fi

# Kill API server
kill $API_PID 2>/dev/null || true
wait $API_PID 2>/dev/null || true

echo ""
echo "=== Test Summary ==="
echo -e "Passed: ${GREEN}$PASSED${NC}"
echo -e "Failed: ${RED}$FAILED${NC}"

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! Deployment is ready.${NC}"
    exit 0
else
    echo -e "${YELLOW}Some tests failed. Check the output above.${NC}"
    exit 1
fi

