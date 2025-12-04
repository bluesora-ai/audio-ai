# Complete Deployment & Testing Guide

## Part 1: Local Testing (Before Deployment)

Test everything locally first to ensure it works before deploying.

### Quick Local Test

```bash
# 1. Setup
cd "D:\work folder\kevino\audio-ai"
python -m venv venv
venv\Scripts\activate  # Windows
pip install --upgrade pip
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy transformers accelerate

# 2. Create test audio
python scripts/create_test_audio.py

# 3. Run demo
python scripts/milestone1_demo.py

# 4. Test API
uvicorn api.main:app --host 127.0.0.1 --port 8000
# In another terminal:
curl http://localhost:8000/health
```

---

## Part 2: Deploy to Ubuntu VPS

### Complete Deployment Steps

```bash
# Step 1: Connect to VPS
ssh user@your-vps-ip

# Step 2: Update system
sudo apt update && sudo apt upgrade -y

# Step 3: Install system dependencies
sudo apt install -y python3 python3-venv python3-dev python3-pip git build-essential ffmpeg libsndfile1 libsndfile1-dev sox libsox-dev pkg-config libhdf5-dev

# Step 4: Upload project (from local machine)
# Option A: Using SCP
scp -r "D:\work folder\kevino\audio-ai" user@your-vps-ip:~/

# Option B: Using Git (if you have repo)
cd ~
git clone <your-repo-url> audio-ai
cd audio-ai

# Step 5: Setup Python environment
cd ~/audio-ai
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel

# Step 6: Install Python packages
pip install numpy soundfile pytest faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy soxr pyyaml tqdm matplotlib seaborn transformers accelerate

# Step 7: Create directories
mkdir -p data/{raw,derived/segments,embeddings,indexes,reports,uploads} models logs
chmod -R 755 data models

# Step 8: Test installation
python3 scripts/create_test_audio.py
python3 scripts/milestone1_demo.py

# Step 9: Start API server
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## Part 3: Test from Local Machine

After deployment, test the API from your local machine.

### Test Scripts

Create these files on your **local machine**:

---

## Quick Test Commands

### From Your Local Machine:

```bash
# Replace your-vps-ip with actual IP address

# 1. Health check
curl http://your-vps-ip:8000/health

# 2. Test root
curl http://your-vps-ip:8000/

# 3. Upload audio file
curl -X POST "http://your-vps-ip:8000/api/v1/provenance-check" \
  -F "file=@test_audio.wav"

# 4. Check status (replace JOB_ID)
curl http://your-vps-ip:8000/api/v1/status/JOB_ID

# 5. Get report
curl http://your-vps-ip:8000/api/v1/reports/JOB_ID > report.json
```

### From Browser:

Open:
```
http://your-vps-ip:8000/docs
```

This shows interactive API documentation where you can test all endpoints.

---

## Complete Testing Workflow

### 1. Test Locally First
### 2. Deploy to VPS
### 3. Test from Local Machine
### 4. Verify Everything Works

---

## Expected Test Results

✅ All components working
✅ API responding
✅ File upload successful
✅ Processing completes
✅ Reports generated

