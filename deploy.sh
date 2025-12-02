#!/bin/bash
# Quick deployment script for Ubuntu VPS
set -e

echo "=== Audio Provenance System - Quick Deployment ==="
echo ""

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
   echo "Please do not run as root. Use a regular user with sudo privileges."
   exit 1
fi

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Step 1: Update system
echo -e "${YELLOW}[1/7]${NC} Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Step 2: Install system dependencies
echo -e "${YELLOW}[2/7]${NC} Installing system dependencies..."
sudo apt install -y \
    git \
    curl \
    wget \
    build-essential \
    python3.10 \
    python3.10-venv \
    python3-pip \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    sox \
    libsox-dev \
    || echo "Some packages may already be installed"

# Step 3: Create virtual environment
echo -e "${YELLOW}[3/7]${NC} Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3.10 -m venv venv
    echo -e "${GREEN}✓${NC} Virtual environment created"
else
    echo -e "${GREEN}✓${NC} Virtual environment already exists"
fi

# Step 4: Activate venv and install Python packages
echo -e "${YELLOW}[4/7]${NC} Installing Python packages..."
source venv/bin/activate
pip install --upgrade pip setuptools wheel

if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo -e "${GREEN}✓${NC} Python packages installed"
else
    echo "Warning: requirements.txt not found!"
fi

# Step 5: Create necessary directories
echo -e "${YELLOW}[5/7]${NC} Creating data directories..."
mkdir -p data/{raw,derived/segments,embeddings,indexes,reports,uploads,training/{human,ai},test}
mkdir -p models
mkdir -p logs
echo -e "${GREEN}✓${NC} Directories created"

# Step 6: Set permissions
echo -e "${YELLOW}[6/7]${NC} Setting permissions..."
chmod -R 755 data models
echo -e "${GREEN}✓${NC} Permissions set"

# Step 7: Verify installation
echo -e "${YELLOW}[7/7]${NC} Verifying installation..."
python3 -c "import torch; print(f'PyTorch: {torch.__version__}')" || echo "Warning: PyTorch not installed"
python3 -c "import faiss; print('FAISS: OK')" || echo "Warning: FAISS not installed"
python3 -c "from src.pipeline import PipelineOrchestrator; print('Pipeline: OK')" || echo "Warning: Pipeline import failed"

echo ""
echo -e "${GREEN}=== Deployment Complete! ==="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Upload test audio to: data/raw/test_audio.wav"
echo "3. Run demo: python scripts/run_demo_m2.py"
echo "4. Start API: uvicorn api.main:app --host 0.0.0.0 --port 8000"
echo ""
echo "For detailed instructions, see: DEPLOYMENT_GUIDE.md"

