# Testing & Deployment Quick Reference

## 🏠 Local Testing (Before Deployment)

### Quick Test

```bash
# 1. Activate venv
cd "D:\work folder\kevino\audio-ai"
venv\Scripts\activate

# 2. Test everything
python test_local.py

# OR manually:
python scripts/create_test_audio.py
python scripts/milestone1_demo.py
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

**Expected:** All tests pass, files generated, API responds

---

## 🖥️ Deploy to Ubuntu VPS

### One-Command Setup

```bash
# On VPS:
cd ~/audio-ai
chmod +x setup_vps.sh
./setup_vps.sh
```

### Manual Setup

```bash
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
# Health check
curl http://your-vps-ip:8000/health

# Upload file
curl -X POST "http://your-vps-ip:8000/api/v1/provenance-check" -F "file=@test.wav"

# Get report (replace JOB_ID)
curl http://your-vps-ip:8000/api/v1/reports/JOB_ID > report.json
```

### Automated Test

```bash
# Edit test_remote.py - set VPS_IP
python test_remote.py test_audio.wav
```

### Browser Test

Open: `http://your-vps-ip:8000/docs`

---

## ✅ Success Checklist

- [ ] Local tests pass
- [ ] Project uploaded to VPS
- [ ] Packages installed on VPS
- [ ] API server running
- [ ] Can connect from local
- [ ] File upload works
- [ ] Reports generated

---

**See COMPLETE_DEPLOYMENT_GUIDE.md for detailed instructions!**

