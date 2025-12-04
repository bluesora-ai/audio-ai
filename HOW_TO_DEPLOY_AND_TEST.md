# How to Deploy and Test - Complete Guide

## 📖 Three Simple Steps

1. **Test Locally** → Make sure it works on your computer
2. **Deploy to VPS** → Setup on Ubuntu server  
3. **Test Remotely** → Test from your local machine

---

## Step 1: Test Locally (Your Computer)

### Windows Commands

```cmd
REM Navigate to project
cd "D:\work folder\kevino\audio-ai"

REM Activate virtual environment
venv\Scripts\activate

REM Install packages
pip install --upgrade pip
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy transformers accelerate

REM Create test audio
python scripts\create_test_audio.py

REM Run demo
python scripts\milestone1_demo.py

REM Start API server
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### Test API (Another Terminal)

```cmd
curl http://localhost:8000/health
```

**✅ If this works → Ready for VPS!**

---

## Step 2: Deploy to Ubuntu VPS

### 2.1 Upload Project to VPS

**From your local Windows machine:**

```cmd
REM Upload project to VPS
scp -r "D:\work folder\kevino\audio-ai" user@your-vps-ip:~/
```

**Or use Git:**
```bash
# On VPS
cd ~
git clone <your-repo-url> audio-ai
```

### 2.2 Setup on VPS

**SSH into VPS:**
```bash
ssh user@your-vps-ip
```

**Run these commands on VPS:**

```bash
# 1. Update system
sudo apt update && sudo apt upgrade -y

# 2. Install system packages
sudo apt install -y python3 python3-venv python3-dev python3-pip git build-essential ffmpeg libsndfile1 libsndfile1-dev sox libsox-dev pkg-config libhdf5-dev

# 3. Navigate to project
cd ~/audio-ai

# 4. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 5. Install Python packages (takes 10-20 minutes)
pip install --upgrade pip
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy soxr pyyaml tqdm matplotlib seaborn transformers accelerate

# 6. Create directories
mkdir -p data/{raw,derived/segments,embeddings,indexes,reports,uploads} models logs
chmod -R 755 data models

# 7. Test installation
python3 scripts/create_test_audio.py
python3 scripts/milestone1_demo.py

# 8. Open firewall
sudo ufw allow 8000/tcp

# 9. Start API server
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### 2.3 Run as Background Service (Optional)

```bash
# Create service file
sudo nano /etc/systemd/system/audio-provenance.service
```

**Paste this (replace `user` with your username):**
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

**Enable service:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable audio-provenance
sudo systemctl start audio-provenance
sudo systemctl status audio-provenance
```

---

## Step 3: Test from Local Machine

### 3.1 Basic Tests

**From your Windows computer:**

```cmd
REM Replace your-vps-ip with actual IP

REM 1. Health check
curl http://your-vps-ip:8000/health

REM 2. Test root
curl http://your-vps-ip:8000/
```

### 3.2 Upload Audio File

```cmd
REM Upload file for processing
curl -X POST "http://your-vps-ip:8000/api/v1/provenance-check" -F "file=@test_audio.wav"

REM Response: {"job_id": "abc123...", "status": "processing"}
```

### 3.3 Check Status

```cmd
REM Replace JOB_ID with job_id from upload response
curl http://your-vps-ip:8000/api/v1/status/JOB_ID
```

### 3.4 Get Report

```cmd
REM Get provenance report
curl http://your-vps-ip:8000/api/v1/reports/JOB_ID > report.json

REM View report
type report.json
```

### 3.5 Browser Test

**Open in browser:**
```
http://your-vps-ip:8000/docs
```

This shows interactive API documentation where you can test all endpoints!

---

## 📋 Quick Command Reference

### Local Testing (Windows)
```cmd
cd "D:\work folder\kevino\audio-ai"
venv\Scripts\activate
python scripts\create_test_audio.py
python scripts\milestone1_demo.py
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### VPS Deployment (Linux)
```bash
cd ~/audio-ai
source venv/bin/activate
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy transformers accelerate
python3 scripts/create_test_audio.py
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Remote Testing (Windows)
```cmd
curl http://your-vps-ip:8000/health
curl -X POST "http://your-vps-ip:8000/api/v1/provenance-check" -F "file=@test.wav"
```

---

## 🔍 Troubleshooting

### Can't Connect to VPS

```bash
# On VPS - check firewall
sudo ufw status
sudo ufw allow 8000/tcp

# Check if API is running
curl http://localhost:8000/health
```

### API Not Responding

```bash
# Check service status
sudo systemctl status audio-provenance

# View logs
sudo journalctl -u audio-provenance -f

# Restart service
sudo systemctl restart audio-provenance
```

### Upload Fails

- Check file size (should be reasonable)
- Check file format (WAV works best)
- Check API logs for errors

---

## ✅ Success Checklist

- [ ] Local tests pass
- [ ] Project uploaded to VPS
- [ ] All packages installed
- [ ] API server running
- [ ] Firewall allows port 8000
- [ ] Can connect from local machine
- [ ] Health check works
- [ ] File upload works
- [ ] Reports generated

---

## 🎯 Summary

**Local:** Test on your computer first  
**VPS:** Upload and setup on server  
**Remote:** Test the deployed API from your computer  

**That's it! Follow these 3 steps.**

