# 🚀 Complete Run Guide - Deploy & Test with Visual Results

This guide shows you how to:
1. **Run locally** (test on your computer)
2. **Deploy to Ubuntu VPS** (production server)
3. **Test with visual GUI** (see results visually)

---

## Part 1: Run Locally (Windows)

### Step 1: Setup Environment

```cmd
REM Navigate to project
cd "D:\work folder\kevino\audio-ai"

REM Create virtual environment (if not exists)
python -m venv venv

REM Activate virtual environment
venv\Scripts\activate

REM Upgrade pip
pip install --upgrade pip
```

### Step 2: Install Dependencies

```cmd
REM Install all required packages
pip install -r requirements.txt

REM Or install individually if needed:
pip install numpy soundfile faiss-cpu torch torchaudio demucs fastapi uvicorn[standard] pydantic scikit-learn librosa scipy soxr pyyaml tqdm matplotlib seaborn transformers accelerate python-multipart requests psutil
```

### Step 3: Create Test Audio

```cmd
python scripts/create_test_audio.py
```

This creates `data/raw/test_audio.wav`

### Step 4: Test Pipeline Locally

```cmd
REM Run the complete pipeline demo
python scripts/run_demo_m2.py
```

**Expected Output:**
- Creates segments
- Separates stems
- Generates embeddings
- Searches for matches
- Classifies AI vs Human
- Generates provenance report with evidence

### Step 5: Start Local API Server

```cmd
REM Start API server
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

**Keep this terminal open!**

### Step 6: Test Local API

**In another terminal:**
```cmd
REM Health check
curl http://localhost:8000/health

REM Should return: {"status": "healthy"}
```

**Or open in browser:**
- API Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

---

## Part 2: Deploy to Ubuntu VPS

### Step 1: Upload Project to VPS

**From your local Windows machine:**

**Option A: Using SCP**
```cmd
scp -r "D:\work folder\kevino\audio-ai" user@your-vps-ip:~/
```

**Option B: Using Git (Recommended)**
```bash
# On VPS
ssh user@your-vps-ip
cd ~
git clone https://github.com/bluesora-ai/audio-ai.git
cd audio-ai
git checkout master  # or main
```

### Step 2: SSH into VPS

```bash
ssh user@your-vps-ip
```

### Step 3: Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y \
    python3 \
    python3-venv \
    python3-dev \
    python3-pip \
    git \
    build-essential \
    ffmpeg \
    libsndfile1 \
    libsndfile1-dev \
    sox \
    libsox-dev \
    pkg-config \
    libhdf5-dev
```

### Step 4: Setup Python Environment

```bash
# Navigate to project
cd ~/audio-ai

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 5: Install Python Packages

```bash
# Install all packages from requirements.txt
pip install -r requirements.txt

# This will take 10-20 minutes. Wait for completion.
```

**If OpenL3 fails, it's OK - MERT is the primary model:**
```bash
pip install openl3 --timeout=600 || echo "OpenL3 skipped (MERT is primary)"
```

### Step 6: Create Directories

```bash
# Create all necessary directories
mkdir -p data/{raw,derived/segments,embeddings,indexes,reports,uploads,processing} models logs manifests

# Set permissions
chmod -R 755 data models
```

### Step 7: Test Installation

```bash
# Create test audio
python3 scripts/create_test_audio.py

# Test pipeline import
python3 -c "from src.pipeline import PipelineOrchestrator; print('✓ Installation OK')"

# Run demo (optional)
python3 scripts/run_demo_m2.py
```

### Step 8: Configure Firewall

```bash
# Allow port 8000
sudo ufw allow 8000/tcp

# Check firewall status
sudo ufw status
```

### Step 9: Start API Server

**Option A: Test Run (Foreground)**
```bash
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

**Option B: Background Process**
```bash
source venv/bin/activate
nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > logs/api.log 2>&1 &

# Check if running
ps aux | grep uvicorn
tail -f logs/api.log
```

**Option C: Systemd Service (Production - Recommended)**

Create service file:
```bash
sudo nano /etc/systemd/system/audio-provenance.service
```

Paste this (replace `user` with your username):
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

### Step 10: Verify VPS Deployment

```bash
# Test from VPS itself
curl http://localhost:8000/health

# Should return: {"status": "healthy"}
```

---

## Part 3: Visual Testing with GUI App

### Step 1: Update VPS IP in GUI App

**Edit `gui_test_app.py` on your local machine:**

```python
# Line 12: Update with your VPS IP
VPS_IP = "78.46.37.169"  # Replace with your VPS IP
BASE_URL = f"http://{VPS_IP}:8000"
```

### Step 2: Run GUI App Locally

```cmd
REM On your Windows machine
cd "D:\work folder\kevino\audio-ai"
venv\Scripts\activate
python gui_test_app.py
```

### Step 3: Use the GUI App

**The GUI App provides:**

1. **Connection Panel**
   - VPS URL input
   - Health check button
   - Connection status

2. **File Upload**
   - Browse and select audio file
   - Upload button
   - Upload progress

3. **Processing Status**
   - Job ID display
   - Status updates (processing/completed/failed)
   - Progress bar

4. **Results Display**
   - Complete provenance report
   - Per-segment analysis
   - AI probabilities
   - Match information
   - Fusion scores
   - Risk flags

5. **Evidence Viewing**
   - Links to audio snippets
   - Links to spectrograms
   - Download buttons

### Step 4: Visual Test Workflow

1. **Connect to VPS**
   - Enter VPS IP: `78.46.37.169` (or your IP)
   - Click "Check Health"
   - Should show: ✅ "Connected"

2. **Upload Audio File**
   - Click "Browse" and select an audio file (WAV, MP3, FLAC)
   - Click "Upload & Process"
   - Wait for processing (may take 1-5 minutes)

3. **View Results**
   - Report appears in the text area
   - Shows:
     - Overall summary
     - Per-segment analysis
     - AI probabilities
     - Match details
     - Fusion scores
     - Risk flags

4. **Download Report**
   - Click "Download Report" to save JSON
   - Click "Open Report Location" to view evidence files

### Step 5: View Evidence Files

After processing, evidence files are generated:

**On VPS:**
```bash
# Navigate to processing directory
cd ~/audio-ai/data/processing

# Find your job directory
ls -la

# View evidence
cd <job_id>/evidence
ls -la

# Files include:
# - probe_snippet.wav (audio snippet)
# - probe_spectrogram.png (spectrogram)
# - source_snippet_*.wav (matched source snippets)
# - source_spectrogram_*.png (matched source spectrograms)
```

**Download evidence files:**
```bash
# From your local machine
scp -r user@your-vps-ip:~/audio-ai/data/processing/<job_id>/evidence ./
```

---

## Part 4: Command-Line Testing (Alternative)

### Test from Local Machine

**Basic Tests:**
```cmd
REM Replace your-vps-ip with actual IP

REM 1. Health check
curl http://your-vps-ip:8000/health

REM 2. Root endpoint
curl http://your-vps-ip:8000/

REM 3. API docs (open in browser)
REM http://your-vps-ip:8000/docs
```

### Upload and Process File

```cmd
REM Upload audio file
curl -X POST "http://your-vps-ip:8000/api/v1/provenance-check" -F "file=@test_audio.wav"

REM Response:
REM {"job_id": "abc123...", "status": "processing", "message": "..."}
```

### Check Status

```cmd
REM Replace JOB_ID with actual job_id
curl http://your-vps-ip:8000/api/v1/status/JOB_ID
```

### Download Report

```cmd
REM Download complete report
curl http://your-vps-ip:8000/api/v1/reports/JOB_ID > report.json

REM View report
type report.json
```

### Use Python Test Script

```cmd
REM Run comprehensive test
python test_vps_complete.py data/raw/test_audio.wav
```

---

## Part 5: Understanding the Results

### Report Structure

The provenance report includes:

1. **Overall Summary**
   - `overall_verification_status`: "verified" | "suspicious" | "high_risk"
   - `recommended_action`: Action to take
   - `overall_ai_probability`: Overall AI probability
   - `segments_flagged_ai`: Number of flagged segments

2. **Per-Segment Analysis**
   - `segment_id`: Unique segment identifier
   - `start` / `end`: Time range
   - `stems[]`: Per-stem analysis
     - `classifier.ai_probability`: AI probability
     - `fusion_score`: Combined fusion score
     - `consecutive_matches`: Consecutive match count
     - `final_decision`: "ai" | "human"
     - `confidence_bucket`: "high" | "medium" | "low"
   - `matches[]`: Top matches with similarity scores
   - `risk_flag`: "high" | "medium" | "low"

3. **Stems Summary**
   - Per-stem aggregated statistics
   - `aggregated_ai_score`: Average fusion score
   - `matches_found`: Number of matches
   - `risk_flags`: Overall risk level

4. **Evidence Files**
   - Audio snippets (probe and matched sources)
   - Spectrograms (visual frequency analysis)
   - Paths included in report

5. **Model Provenance**
   - `pipeline_version`: Git commit hash
   - `fingerprint_model_checksum`: Model hash
   - `index_config`: Index configuration
   - `audit.processing_time_sec`: Processing duration

### Performance Report

After processing, check `perf_report.json`:

```bash
# On VPS
cat ~/audio-ai/data/processing/<job_id>/perf_report.json
```

**Includes:**
- Total processing time
- Embedding throughput
- Memory usage
- CPU usage
- Compliance with targets

---

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to VPS
```bash
# Check if API is running
ps aux | grep uvicorn

# Check firewall
sudo ufw status

# Check if port is listening
sudo netstat -tlnp | grep 8000
```

### Processing Errors

**Problem:** Processing fails
```bash
# Check logs
tail -f logs/api.log

# Check processing directory
ls -la data/processing/

# Verify models are loaded
python3 -c "from src.stage3_embedding import EmbeddingGenerator; e = EmbeddingGenerator(); print(e.get_model_info())"
```

### GUI App Issues

**Problem:** GUI app cannot connect
- Verify VPS IP is correct
- Check firewall allows port 8000
- Verify API is running on VPS
- Check network connectivity: `ping your-vps-ip`

**Problem:** Timeout errors
- Increase `TIMEOUT` in `gui_test_app.py` (line 14)
- Increase `MAX_WAIT` (line 16)
- Check VPS resources (CPU, memory)

---

## Quick Reference

### Local Testing
```cmd
venv\Scripts\activate
python scripts/create_test_audio.py
python scripts/run_demo_m2.py
uvicorn api.main:app --host 127.0.0.1 --port 8000
python gui_test_app.py
```

### VPS Deployment
```bash
cd ~/audio-ai
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Visual Testing
```cmd
python gui_test_app.py
# Enter VPS IP, upload file, view results
```

---

## Next Steps

1. ✅ **Test locally** - Verify everything works
2. ✅ **Deploy to VPS** - Setup production server
3. ✅ **Test with GUI** - Visual verification
4. ✅ **Review reports** - Check evidence files
5. ✅ **Performance check** - Review perf_report.json

**You're all set! 🎉**

