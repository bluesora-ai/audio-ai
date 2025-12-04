# Simple Deployment & Testing Guide

## 🎯 Quick Summary

1. **Test Locally First** → Make sure it works on your machine
2. **Deploy to VPS** → Upload and setup on Ubuntu server
3. **Test from Local** → Test the deployed API from your computer

---

## Part 1: Test Locally (Your Computer)

### Step 1: Setup

```bash
cd "D:\work folder\kevino\audio-ai"
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
```

### Step 2: Install Packages

```bash
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy transformers accelerate
```

### Step 3: Test

```bash
# Create test audio
python scripts/create_test_audio.py

# Run demo
python scripts/milestone1_demo.py

# Start API
uvicorn api.main:app --host 127.0.0.1 --port 8000

# Test (in another terminal)
curl http://localhost:8000/health
```

**✅ If all work → Ready to deploy!**

---

## Part 2: Deploy to VPS

### Step 1: Upload Project

**From your local machine:**
```bash
scp -r "D:\work folder\kevino\audio-ai" user@your-vps-ip:~/
```

### Step 2: On VPS - Complete Setup

**SSH into VPS:**
```bash
ssh user@your-vps-ip
```

**Run these commands on VPS:**
```bash
# Install system packages
sudo apt update
sudo apt install -y python3 python3-venv python3-pip git build-essential ffmpeg libsndfile1 libsndfile1-dev

# Setup project
cd ~/audio-ai
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# Install Python packages (takes 10-20 min)
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy transformers accelerate

# Create directories
mkdir -p data/{raw,derived/segments,embeddings,indexes,reports,uploads} models logs

# Test
python3 scripts/create_test_audio.py
python3 scripts/milestone1_demo.py

# Start API
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Step 3: Open Firewall

```bash
sudo ufw allow 8000/tcp
```

---

## Part 3: Test from Local Machine

### Quick Tests

**From your local computer:**

```bash
# Replace your-vps-ip with actual IP

# 1. Health check
curl http://your-vps-ip:8000/health

# 2. Upload file
curl -X POST "http://your-vps-ip:8000/api/v1/provenance-check" \
  -F "file=@test_audio.wav"

# 3. Check status (use job_id from upload)
curl http://your-vps-ip:8000/api/v1/status/JOB_ID

# 4. Get report
curl http://your-vps-ip:8000/api/v1/reports/JOB_ID > report.json
```

### Browser Test

Open in browser:
```
http://your-vps-ip:8000/docs
```

Click "Try it out" to test endpoints!

---

## 📝 Complete Command List

### Local Testing
```bash
cd "D:\work folder\kevino\audio-ai"
venv\Scripts\activate
python scripts/create_test_audio.py
python scripts/milestone1_demo.py
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### VPS Deployment
```bash
cd ~/audio-ai
source venv/bin/activate
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy transformers accelerate
mkdir -p data/{raw,derived/segments,embeddings,indexes,reports,uploads} models logs
python3 scripts/create_test_audio.py
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Remote Testing
```bash
curl http://your-vps-ip:8000/health
curl -X POST "http://your-vps-ip:8000/api/v1/provenance-check" -F "file=@test.wav"
```

---

That's it! Follow these steps in order.

