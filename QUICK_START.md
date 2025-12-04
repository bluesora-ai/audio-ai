# ⚡ Quick Start Guide

## 🎯 Three Simple Steps

### 1️⃣ Deploy to VPS (One-Time Setup)

**SSH to your VPS and run:**
```bash
# Clone or upload project
cd ~
git clone https://github.com/bluesora-ai/audio-ai.git
cd audio-ai

# Setup
sudo apt update && sudo apt install -y python3 python3-venv python3-pip git build-essential ffmpeg libsndfile1 libsndfile1-dev
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create directories
mkdir -p data/{raw,indexes,reports,uploads,processing} models logs

# Start API
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
```

### 2️⃣ Test with Visual GUI

**On your local Windows machine:**
```cmd
cd "D:\work folder\kevino\audio-ai"
venv\Scripts\activate
python gui_test_app.py
```

**In the GUI:**
1. Enter VPS IP: `78.46.37.169` (or your IP)
2. Click "Check Health"
3. Click "Browse" and select audio file
4. Click "Upload & Process"
5. Wait for results (1-5 minutes)
6. View complete report with visual results!

### 3️⃣ View Results

**The GUI shows:**
- ✅ Overall verification status
- ✅ Per-segment AI probabilities
- ✅ Fusion scores
- ✅ Match details
- ✅ Risk flags
- ✅ Evidence file paths

**Download report:**
- Click "Download Report" to save JSON
- Evidence files (snippets, spectrograms) are on VPS

---

## 🔧 Quick Commands

### Start VPS API
```bash
cd ~/audio-ai
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Test from Local
```cmd
python gui_test_app.py
```

### Check VPS Status
```bash
curl http://localhost:8000/health
```

---

## 📊 What You'll See

### In GUI App:
- **Connection Status**: ✅ Connected / ❌ Failed
- **Processing Status**: Processing → Completed
- **Report Display**: Full JSON report with all details
- **Download Options**: Save report, view evidence

### In Report:
- **Overall Summary**: Verification status, recommended action
- **Per-Segment**: AI probability, fusion score, matches
- **Stems Summary**: Aggregated statistics per stem type
- **Evidence Paths**: Links to audio snippets and spectrograms
- **Performance**: Processing time, throughput metrics

---

## 🆘 Need Help?

- **Connection issues?** Check firewall: `sudo ufw allow 8000/tcp`
- **Processing fails?** Check logs: `tail -f logs/api.log`
- **GUI timeout?** Increase `TIMEOUT` in `gui_test_app.py`

**See `COMPLETE_RUN_GUIDE.md` for detailed instructions!**

