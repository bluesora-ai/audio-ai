# 🎨 Visual Testing Guide - GUI App

## Overview

The GUI App (`gui_test_app.py`) provides a **visual desktop application** for testing the Audio Provenance API. You can upload files, see processing status, and view complete results with visual feedback.

---

## 🚀 Quick Start

### Step 1: Update VPS IP

**Edit `gui_test_app.py` (line 12):**
```python
VPS_IP = "78.46.37.169"  # Replace with your VPS IP
```

### Step 2: Run GUI App

```cmd
cd "D:\work folder\kevino\audio-ai"
venv\Scripts\activate
python gui_test_app.py
```

---

## 📱 GUI Interface Overview

### Main Window Layout

```
┌─────────────────────────────────────────────────┐
│     Audio Provenance Test App                  │
├─────────────────────────────────────────────────┤
│ VPS URL: [http://78.46.37.169:8000        ]    │
│ Audio File: [path/to/file.wav            ] [Browse]│
├─────────────────────────────────────────────────┤
│ [Test Health] [Upload & Process] [Check Status] │
│ [Download Report] [Clear]                       │
├─────────────────────────────────────────────────┤
│ Status: Ready                                   │
│ [Progress Bar]                                  │
│ Job ID: [abc123-def456-...]                    │
├─────────────────────────────────────────────────┤
│ Log Output:                                     │
│ ┌───────────────────────────────────────────┐ │
│ │ {                                          │ │
│ │   "job_id": "...",                         │ │
│ │   "overall_summary": {                     │ │
│ │     "overall_verification_status": "...",   │ │
│ │     "recommended_action": "...",           │ │
│ │     "overall_ai_probability": 0.75         │ │
│ │   },                                        │ │
│ │   "segments": [...],                       │ │
│ │   "stems_summary": [...]                   │ │
│ │ }                                          │ │
│ └───────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
```

---

## 🎯 Step-by-Step Usage

### 1. Connect to VPS

1. **Enter VPS URL** in the text field:
   ```
   http://78.46.37.169:8000
   ```

2. **Click "Test Health"**
   - Status shows: ✅ "Connected" or ❌ "Connection failed"
   - If failed, check:
     - VPS IP is correct
     - API is running on VPS
     - Firewall allows port 8000

### 2. Select Audio File

1. **Click "Browse"** button
2. **Select audio file** (WAV, MP3, FLAC supported)
3. **File path appears** in the text field

### 3. Upload and Process

1. **Click "Upload & Process"**
2. **Progress bar starts** (indeterminate)
3. **Status updates:**
   - "Uploading..."
   - "Processing..."
   - "Waiting for completion..."
   - "Completed!"

4. **Job ID appears** in the Job ID field

### 4. View Results

**The Log Output area shows:**

#### Overall Summary
```json
{
  "overall_summary": {
    "overall_verification_status": "suspicious",
    "recommended_action": "review_recommended",
    "overall_ai_probability": 0.65,
    "segments_flagged_ai": 5,
    "total_segments": 10
  }
}
```

#### Per-Segment Analysis
```json
{
  "segments": [
    {
      "segment_id": "test_audio_seg_0000",
      "start": 0.0,
      "end": 0.5,
      "stems": [{
        "stem_type": "vocals",
        "classifier": {
          "ai_probability": 0.75,
          "calibrated_probability": 0.73
        },
        "fusion_score": 0.68,
        "consecutive_matches": 3,
        "final_decision": "ai",
        "confidence_bucket": "medium",
        "matches": [{
          "source_file_id": "known_ai_track",
          "similarity": 0.85,
          "rank": 1
        }]
      }],
      "risk_flag": "medium"
    }
  ]
}
```

#### Stems Summary
```json
{
  "stems_summary": [
    {
      "stem_type": "vocals",
      "aggregated_ai_score": 0.68,
      "matches_found": 8,
      "risk_flags": "medium"
    }
  ]
}
```

### 5. Download Report

1. **Click "Download Report"**
2. **File saved** as `provenance_report_<job_id>.json`
3. **Open in text editor** to view formatted JSON

---

## 📊 Understanding Results

### Verification Status

- **"verified"** - Low AI probability, likely human
- **"suspicious"** - Medium AI probability, review recommended
- **"high_risk"** - High AI probability, manual review required

### Recommended Actions

- **"no_action_needed"** - File appears authentic
- **"review_recommended"** - Should be reviewed
- **"manual_review_required"** - Requires human verification

### Fusion Scores

- **0.0 - 0.3**: Likely human (low risk)
- **0.3 - 0.7**: Uncertain (medium risk)
- **0.7 - 1.0**: Likely AI (high risk)

### Confidence Buckets

- **"high"**: Very confident in decision
- **"medium"**: Moderately confident
- **"low"**: Low confidence, more evidence needed

### Risk Flags

- **"low"**: Minimal risk
- **"medium"**: Moderate risk, review recommended
- **"high"**: High risk, immediate review required

---

## 🔍 Evidence Files

After processing, evidence files are generated on the VPS:

### Location
```
~/audio-ai/data/processing/<job_id>/evidence/
```

### Files Generated

1. **Audio Snippets**
   - `probe_snippet.wav` - Original segment
   - `source_snippet_0.wav` - Top matched source
   - `source_snippet_1.wav` - Second match
   - `source_snippet_2.wav` - Third match

2. **Spectrograms**
   - `probe_spectrogram.png` - Visual frequency analysis
   - `source_spectrogram_0.png` - Matched source spectrogram
   - `source_spectrogram_1.png` - Second match spectrogram
   - `source_spectrogram_2.png` - Third match spectrogram

### Download Evidence

**From your local machine:**
```cmd
scp -r user@78.46.37.169:~/audio-ai/data/processing/<job_id>/evidence ./
```

**Or use FileZilla/WinSCP:**
- Connect to VPS
- Navigate to `~/audio-ai/data/processing/<job_id>/evidence/`
- Download all files

---

## 🎨 Visual Features

### Color Coding (in JSON)

The report JSON can be viewed with syntax highlighting:
- **Strings**: File paths, IDs
- **Numbers**: Probabilities, scores
- **Booleans**: Flags, status

### Progress Indicators

- **Progress Bar**: Shows processing activity
- **Status Text**: Current operation
- **Job ID**: Unique identifier for tracking

---

## ⚙️ Configuration

### Timeout Settings

**Edit `gui_test_app.py`:**

```python
TIMEOUT = 120  # Upload/processing timeout (seconds)
CONNECT_TIMEOUT = 10  # Connection timeout (seconds)
MAX_WAIT = 600  # Maximum wait for completion (seconds)
```

**For large files or slow connections, increase:**
```python
TIMEOUT = 300  # 5 minutes
MAX_WAIT = 1200  # 20 minutes
```

### VPS URL

**Change VPS IP:**
```python
VPS_IP = "your-vps-ip-here"
BASE_URL = f"http://{VPS_IP}:8000"
```

---

## 🐛 Troubleshooting

### Connection Failed

**Problem:** "Test Health" fails

**Solutions:**
1. Check VPS IP is correct
2. Verify API is running: `curl http://your-vps-ip:8000/health`
3. Check firewall: `sudo ufw status` on VPS
4. Verify network connectivity: `ping your-vps-ip`

### Upload Timeout

**Problem:** Upload times out

**Solutions:**
1. Increase `TIMEOUT` in `gui_test_app.py`
2. Check file size (very large files may need more time)
3. Verify network speed
4. Check VPS resources (CPU, memory)

### Processing Failed

**Problem:** Status shows "failed"

**Solutions:**
1. Check VPS logs: `tail -f logs/api.log`
2. Verify all dependencies installed
3. Check disk space on VPS
4. Review error message in GUI log output

### No Results Displayed

**Problem:** Report area is empty

**Solutions:**
1. Wait for processing to complete
2. Check "Check Status" button
3. Verify job completed successfully
4. Try "Download Report" to save file

---

## 📝 Example Workflow

### Complete Test Session

1. **Start GUI App**
   ```cmd
   python gui_test_app.py
   ```

2. **Connect**
   - Enter VPS URL
   - Click "Test Health"
   - Verify: ✅ "Connected"

3. **Upload File**
   - Click "Browse"
   - Select `test_audio.wav`
   - Click "Upload & Process"
   - Wait 2-5 minutes

4. **View Results**
   - Scroll through JSON report
   - Check overall summary
   - Review per-segment analysis
   - Note fusion scores and risk flags

5. **Download Report**
   - Click "Download Report"
   - Save as `report.json`
   - Open in text editor

6. **Download Evidence**
   ```cmd
   scp -r user@78.46.37.169:~/audio-ai/data/processing/<job_id>/evidence ./
   ```

7. **Review Evidence**
   - Play audio snippets
   - View spectrograms
   - Compare probe vs matched sources

---

## ✅ Success Indicators

### Successful Test Shows:

- ✅ **Connection**: "Connected" status
- ✅ **Upload**: File uploads successfully
- ✅ **Processing**: Status changes to "Completed"
- ✅ **Report**: JSON report displayed
- ✅ **Summary**: Overall verification status shown
- ✅ **Segments**: Per-segment analysis visible
- ✅ **Evidence**: Paths to evidence files included

---

## 🎯 Next Steps

After visual testing:

1. **Review Reports** - Analyze AI probabilities and fusion scores
2. **Check Evidence** - Listen to snippets, view spectrograms
3. **Performance** - Check `perf_report.json` for metrics
4. **Iterate** - Test with different audio files
5. **Production** - Deploy to production if satisfied

**For detailed deployment, see `COMPLETE_RUN_GUIDE.md`!**

