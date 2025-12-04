# 🚀 START HERE - Complete Guide

## Quick Navigation

- **Test Locally First** → Section 1
- **Deploy to VPS** → Section 2  
- **Test from Local** → Section 3

---

## Section 1: Test Locally (Your Computer) 🏠

### Complete Local Test

```bash
# Step 1: Setup
cd "D:\work folder\kevino\audio-ai"
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip

# Step 2: Install packages
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy transformers accelerate

# Step 3: Create test audio
python scripts/create_test_audio.py

# Step 4: Run demo
python scripts/milestone1_demo.py

# Step 5: Test API
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

**In another terminal, test:**
```bash
curl http://localhost:8000/health
```

**✅ Expected:** Returns `{"status": "healthy"}`

---

## Section 2: Deploy to Ubuntu VPS 🖥️

### Upload Project

**From your local machine:**
```bash
scp -r "D:\work folder\kevino\audio-ai" user@your-vps-ip:~/
```

### Setup on VPS

**SSH to VPS and run:**
```bash
# All-in-one setup
cd ~/audio-ai
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git build-essential ffmpeg libsndfile1 libsndfile1-dev
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy transformers accelerate
mkdir -p data/{raw,derived/segments,embeddings,indexes,reports,uploads} models logs
python3 scripts/create_test_audio.py
sudo ufw allow 8000/tcp
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**✅ Expected:** API running on port 8000

---

## Section 3: Test from Local Machine 🌐

### Quick Tests

```bash
# Replace your-vps-ip with actual IP

# 1. Health check
curl http://your-vps-ip:8000/health

# 2. Upload file
curl -X POST "http://your-vps-ip:8000/api/v1/provenance-check" -F "file=@test.wav"

# 3. Browser test
# Open: http://your-vps-ip:8000/docs
```

**✅ Expected:** All endpoints work

---

## 📝 All Commands in One Place

### Local Testing
```bash
cd "D:\work folder\kevino\audio-ai"
venv\Scripts\activate
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy transformers accelerate
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

**Follow these 3 sections in order!**

