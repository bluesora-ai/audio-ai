# Local Testing Guide - Test Before Deploying

Complete guide to test the project locally on your machine before deploying to VPS.

## Prerequisites

- Python 3.10+ installed locally
- Windows/macOS/Linux machine
- Project files downloaded/cloned

---

## Step-by-Step Local Testing

### Step 1: Setup Local Environment

```bash
# Navigate to project directory
cd "D:\work folder\kevino\audio-ai"  # or your path

# Create virtual environment
python -m venv venv

# Activate venv
# Windows (Git Bash):
source venv/Scripts/activate
# Windows (CMD/PowerShell):
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 2: Install Dependencies

```bash
# Install all packages
pip install numpy soundfile pytest faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy soxr pyyaml tqdm matplotlib seaborn transformers accelerate

# Skip OpenL3 if it fails (MERT is primary model)
pip install openl3 --timeout=600 || echo "OpenL3 skipped, using MERT"
```

### Step 3: Create Test Audio

```bash
# Create test audio file
python scripts/create_test_audio.py

# Verify it was created
ls data/raw/test_audio.wav
# or
dir data\raw\test_audio.wav  # Windows
```

### Step 4: Test Each Component

**Test 1: Segmentation**
```bash
python -c "from src.stage2_preprocessing import Segmenter; s = Segmenter(); print('✓ Segmentation OK')"
```

**Test 2: Embeddings**
```bash
python -c "from src.stage3_embedding import EmbeddingGenerator; e = EmbeddingGenerator(); print('✓ Embeddings OK')"
```

**Test 3: FAISS**
```bash
python -c "from src.stage4_indexing import FAISSIndexer; f = FAISSIndexer(); print('✓ FAISS OK')"
```

**Test 4: Pipeline**
```bash
python -c "from src.pipeline import PipelineOrchestrator; print('✓ Pipeline OK')"
```

### Step 5: Run Complete Pipeline

**Option A: Milestone 1 Demo (Basic)**
```bash
python scripts/milestone1_demo.py
```

**Option B: Milestone 2 Demo (Complete)**
```bash
python scripts/run_demo_m2.py
```

### Step 6: Test API Locally

**Start API Server:**
```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

**In another terminal, test API:**
```bash
# Health check
curl http://localhost:8000/health

# Upload file
curl -X POST "http://localhost:8000/api/v1/provenance-check" \
  -F "file=@data/raw/test_audio.wav"
```

---

## Complete Local Test Script

Create `test_local.sh` (Linux/macOS) or `test_local.bat` (Windows):

**For Windows (`test_local.bat`):**
```batch
@echo off
echo === Local Testing ===

cd /d "D:\work folder\kevino\audio-ai"
call venv\Scripts\activate

echo Testing imports...
python -c "from src.pipeline import PipelineOrchestrator; print('✓ Pipeline OK')"

echo Creating test audio...
python scripts\create_test_audio.py

echo Running demo...
python scripts\milestone1_demo.py

echo Starting API server...
start cmd /k "uvicorn api.main:app --host 127.0.0.1 --port 8000"

echo.
echo === Test Complete ===
echo API running at: http://localhost:8000
echo Press Ctrl+C to stop
pause
```

**For Linux/macOS (`test_local.sh`):**
```bash
#!/bin/bash
echo "=== Local Testing ==="

cd "$(dirname "$0")"
source venv/bin/activate

echo "Testing imports..."
python3 -c "from src.pipeline import PipelineOrchestrator; print('✓ Pipeline OK')"

echo "Creating test audio..."
python3 scripts/create_test_audio.py

echo "Running demo..."
python3 scripts/milestone1_demo.py

echo "Starting API server..."
echo "API will run at: http://localhost:8000"
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

---

## Test Checklist

- [ ] Virtual environment created and activated
- [ ] All dependencies installed
- [ ] Test audio created (`data/raw/test_audio.wav`)
- [ ] Milestone 1 demo runs successfully
- [ ] Milestone 2 demo runs successfully
- [ ] API server starts without errors
- [ ] Health endpoint works (`curl http://localhost:8000/health`)
- [ ] File upload works
- [ ] All imports work correctly

---

## Expected Results

**After running `milestone1_demo.py`:**
- ✅ Segments created in `data/derived/segments/`
- ✅ Embeddings created in `data/embeddings/`
- ✅ FAISS index created in `data/indexes/`
- ✅ Console shows success messages

**After running API:**
- ✅ Server starts on port 8000
- ✅ Health check returns `{"status": "healthy"}`
- ✅ Can upload files and get job_id

---

## Troubleshooting Local Issues

**Issue: Port 8000 already in use**
```bash
# Find process
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/macOS

# Kill process or use different port
uvicorn api.main:app --host 127.0.0.1 --port 8001
```

**Issue: Module not found**
```bash
# Make sure venv is activated
# Reinstall dependencies
pip install -r requirements.txt
```

---

Once all local tests pass, you're ready to deploy to VPS!

