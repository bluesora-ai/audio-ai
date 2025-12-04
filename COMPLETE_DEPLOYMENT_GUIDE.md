# Complete Deployment & Testing Guide

## 📋 Overview

This guide covers:
1. **Local Testing** - Test everything on your machine first
2. **VPS Deployment** - Deploy to Ubuntu VPS
3. **Remote Testing** - Test the deployed API from your local machine

---

## Part 1: Test Locally First ⚠️ IMPORTANT

Always test locally before deploying to catch issues early!

### Step 1: Setup Local Environment

```bash
# Navigate to project
cd "D:\work folder\kevino\audio-ai"

# Create/activate venv
python -m venv venv
venv\Scripts\activate  # Windows

# Install dependencies
pip install --upgrade pip
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy transformers accelerate
```

### Step 2: Run Automated Local Test

```bash
# Run complete test script
python test_local.py

# This will test:
# - All imports
# - Test audio creation
# - Milestone 1 demo
# - File generation
```

### Step 3: Manual Local Tests

```bash
# Create test audio
python scripts/create_test_audio.py

# Run basic demo
python scripts/milestone1_demo.py

# Start API
uvicorn api.main:app --host 127.0.0.1 --port 8000

# Test API (in another terminal)
curl http://localhost:8000/health
```

### Step 4: Verify Local Results

Check these directories exist and have files:
- ✅ `data/raw/test_audio.wav` - Test audio created
- ✅ `data/derived/segments/` - Segments created
- ✅ `data/embeddings/` - Embeddings created
- ✅ `data/indexes/faiss_index.bin` - Index created

**Once all local tests pass → Ready to deploy!**

---

## Part 2: Deploy to Ubuntu VPS

### Step 1: Upload Project to VPS

**From your local machine:**

```bash
# Upload entire project
scp -r "D:\work folder\kevino\audio-ai" user@your-vps-ip:~/

# Or if you have Git repo:
# SSH to VPS first, then:
cd ~
git clone <your-repo-url> audio-ai
```

### Step 2: Connect to VPS and Setup

```bash
# SSH into VPS
ssh user@your-vps-ip

# Navigate to project
cd ~/audio-ai

# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-venv python3-dev python3-pip git build-essential ffmpeg libsndfile1 libsndfile1-dev sox libsox-dev pkg-config libhdf5-dev

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Python Dependencies

```bash
# Install all packages (takes 10-20 minutes)
pip install numpy soundfile pytest faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy soxr pyyaml tqdm matplotlib seaborn transformers accelerate

# Skip OpenL3 if it fails (MERT is primary model)
pip install openl3 --timeout=600 || echo "OpenL3 skipped"
```

### Step 4: Create Directories and Test

```bash
# Create directories
mkdir -p data/{raw,derived/segments,embeddings,indexes,reports,uploads} models logs
chmod -R 755 data models

# Test installation
python3 -c "from src.pipeline import PipelineOrchestrator; print('✓ OK')"

# Create test audio
python3 scripts/create_test_audio.py

# Run demo
python3 scripts/milestone1_demo.py
```

### Step 5: Start API Server

**Option A: Test Run (Foreground)**
```bash
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Option B: Background Process**
```bash
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &

# Check if running
ps aux | grep uvicorn
tail -f logs/api.log
```

**Option C: Systemd Service (Production)**

Create service file:
```bash
sudo nano /etc/systemd/system/audio-provenance.service
```

Paste (replace `user` and paths):
```ini
[Unit]
Description=Audio Provenance API
After=network.target

[Service]
Type=simple
User=user
WorkingDirectory=/home/user/audio-ai
Environment="PATH=/home/user/audio-ai/venv/bin"
ExecStart=/home/user/audio-ai/venv/bin/uvicorn api.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable audio-provenance
sudo systemctl start audio-provenance
sudo systemctl status audio-provenance
```

### Step 6: Configure Firewall

```bash
# Allow port 8000
sudo ufw allow 8000/tcp
sudo ufw status
```

### Step 7: Test on VPS

```bash
# Test from VPS itself
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

---

## Part 3: Test from Local Machine

### Step 1: Test Basic Connectivity

**From your local machine:**

```bash
# Replace your-vps-ip with actual IP

# Test if VPS is accessible
ping your-vps-ip

# Test health endpoint
curl http://your-vps-ip:8000/health

# Should return: {"status": "healthy"}
```

### Step 2: Test All Endpoints

**Quick Tests:**
```bash
# 1. Health check
curl http://your-vps-ip:8000/health

# 2. Root endpoint
curl http://your-vps-ip:8000/

# 3. API docs (open in browser)
# http://your-vps-ip:8000/docs
```

### Step 3: Test File Upload

```bash
# Upload audio file
curl -X POST "http://your-vps-ip:8000/api/v1/provenance-check" \
  -F "file=@test_audio.wav"

# Response will be JSON:
# {"job_id": "abc123...", "status": "processing", "message": "..."}
```

**From Windows PowerShell:**
```powershell
# Navigate to folder with audio file
cd "D:\path\to\audio"

# Upload
curl.exe -X POST "http://your-vps-ip:8000/api/v1/provenance-check" `
  -F "file=@test_audio.wav"
```

### Step 4: Check Job Status

```bash
# Replace JOB_ID with actual job_id from upload response
curl http://your-vps-ip:8000/api/v1/status/JOB_ID

# Response:
# {"status": "processing"} or {"status": "completed", "report_path": "..."}
```

### Step 5: Get Provenance Report

```bash
# After job completes
curl http://your-vps-ip:8000/api/v1/reports/JOB_ID > report.json

# View report
cat report.json  # Linux/macOS
type report.json  # Windows
```

### Step 6: Automated Remote Test

**Use the test script:**

```bash
# Edit test_remote.py first - set VPS_IP = "your-actual-vps-ip"

# Then run:
python test_remote.py test_audio.wav

# This will automatically:
# - Test health endpoint
# - Upload file
# - Check status
# - Download report
```

---

## Complete Test Workflow

### Phase 1: Local Testing ✅

```bash
# 1. Setup
cd "D:\work folder\kevino\audio-ai"
venv\Scripts\activate
pip install -r requirements.txt

# 2. Test
python test_local.py

# 3. Manual test
python scripts/milestone1_demo.py
uvicorn api.main:app --host 127.0.0.1 --port 8000
curl http://localhost:8000/health
```

### Phase 2: VPS Deployment 🚀

```bash
# On VPS:
cd ~/audio-ai
source venv/bin/activate
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy transformers accelerate
python3 scripts/create_test_audio.py
python3 scripts/milestone1_demo.py
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Phase 3: Remote Testing 🌐

```bash
# From local machine:
curl http://your-vps-ip:8000/health
python test_remote.py test_audio.wav
```

---

## Troubleshooting

### Local Testing Issues

**Port already in use:**
```bash
# Find and kill process
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Linux/macOS
```

**Import errors:**
```bash
# Reinstall packages
pip install -r requirements.txt
```

### VPS Deployment Issues

**Can't connect to VPS:**
```bash
# Check firewall
sudo ufw status
sudo ufw allow 8000/tcp

# Check if service is running
sudo systemctl status audio-provenance
```

**API not responding:**
```bash
# Check logs
sudo journalctl -u audio-provenance -f

# Restart service
sudo systemctl restart audio-provenance
```

### Remote Testing Issues

**Connection refused:**
- Check VPS firewall
- Verify API is running
- Check VPS IP address

**Upload fails:**
- Check file size limits
- Verify file format (WAV)
- Check API logs

---

## Success Criteria

✅ **Local Testing:**
- All imports work
- Demo runs successfully
- Files generated correctly
- API responds

✅ **VPS Deployment:**
- All packages installed
- API server running
- Can access from VPS

✅ **Remote Testing:**
- Can connect from local machine
- File upload works
- Processing completes
- Reports generated

---

## Quick Reference

### Local Testing
```bash
python test_local.py
python scripts/milestone1_demo.py
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### VPS Deployment
```bash
cd ~/audio-ai && source venv/bin/activate && uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Remote Testing
```bash
curl http://your-vps-ip:8000/health
python test_remote.py test_audio.wav
```

---

**Ready to deploy!** Follow the phases in order and test each step.

