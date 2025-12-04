#!/bin/bash
# Complete VPS setup script for Audio Provenance System
set -e

echo "=========================================="
echo "Audio Provenance System - VPS Setup"
echo "=========================================="
echo

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Check if running in project directory
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}ERROR: requirements.txt not found!${NC}"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo "[1/8] Updating system packages..."
sudo apt update
sudo apt upgrade -y

echo -e "${GREEN}✓${NC} System updated"
echo

echo "[2/8] Installing system dependencies..."
sudo apt install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    git \
    wget \
    curl \
    build-essential \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    sox \
    libsox-dev \
    pkg-config \
    libhdf5-dev

echo -e "${GREEN}✓${NC} System dependencies installed"
echo

echo "[3/8] Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${YELLOW}⚠${NC} Virtual environment already exists"
fi

echo "[4/8] Activating virtual environment..."
source venv/bin/activate

echo "[5/8] Upgrading pip..."
pip install --upgrade pip setuptools wheel

echo "[6/8] Installing Python packages (this may take 10-20 minutes)..."
pip install numpy soundfile pytest faiss-cpu torch torchaudio demucs fastapi "uvicorn[standard]" pydantic scikit-learn librosa scipy soxr pyyaml tqdm matplotlib seaborn transformers accelerate

echo -e "${GREEN}✓${NC} Python packages installed"
echo

echo "[7/8] Creating directories..."
mkdir -p data/{raw,derived/segments,embeddings,indexes,reports,uploads,training/{human,ai},test}
mkdir -p models logs
chmod -R 755 data models

echo -e "${GREEN}✓${NC} Directories created"
echo

echo "[8/8] Testing installation..."
python3 -c "from src.pipeline import PipelineOrchestrator; print('✓ Pipeline OK')" || {
    echo -e "${YELLOW}⚠${NC} Import test failed, but continuing..."
}

echo
echo "=========================================="
echo -e "${GREEN}SETUP COMPLETE!${NC}"
echo "=========================================="
echo
echo "Next steps:"
echo "1. Create test audio:  python3 scripts/create_test_audio.py"
echo "2. Run demo:           python3 scripts/milestone1_demo.py"
echo "3. Start API:          uvicorn api.main:app --host 0.0.0.0 --port 8000"
echo
echo "To activate venv later:"
echo "  source venv/bin/activate"
echo

