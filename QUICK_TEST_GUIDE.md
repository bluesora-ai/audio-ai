# Quick Testing Guide

## 🏠 Local Testing (Before Deployment)

### Quick Start

```bash
# 1. Activate venv
cd "D:\work folder\kevino\audio-ai"
venv\Scripts\activate  # Windows

# 2. Create test audio
python scripts/create_test_audio.py

# 3. Run demo
python scripts/milestone1_demo.py

# 4. Test API
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### Automated Test Script

```bash
# Run complete local test
python test_local.py
```

---

## 🖥️ Deploy to VPS

### Complete Deployment

```bash
# On VPS:
cd ~/audio-ai
source venv/bin/activate
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy transformers accelerate
mkdir -p data/{raw,derived/segments,embeddings,indexes,reports,uploads} models logs
python3 scripts/create_test_audio.py
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

---

## 🌐 Test from Local Machine

### Quick Test

```bash
# Replace your-vps-ip with actual IP

# 1. Health check
curl http://your-vps-ip:8000/health

# 2. Upload file
curl -X POST "http://your-vps-ip:8000/api/v1/provenance-check" \
  -F "file=@test_audio.wav"

# 3. Get report (replace JOB_ID)
curl http://your-vps-ip:8000/api/v1/reports/JOB_ID > report.json
```

### Automated Test Script

```bash
# Edit test_remote.py - set VPS_IP
# Then run:
python test_remote.py test_audio.wav
```

---

## ✅ Complete Checklist

- [ ] Local tests pass
- [ ] Project deployed to VPS
- [ ] API server running on VPS
- [ ] Can connect from local machine
- [ ] File upload works
- [ ] Reports generated

