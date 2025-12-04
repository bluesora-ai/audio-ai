# Complete Local Verification Guide

## Overview

This guide shows you how to **test and verify the deployed VPS system from your local machine**, ensuring all requirements are met.

---

## Prerequisites

1. **VPS is running** with API accessible at `http://78.46.37.169:8000`
2. **Local machine** with Python 3.10+
3. **Test audio file** (WAV format recommended)

---

## Quick Start

### 1. Install Test Dependencies

```bash
# On your local machine
cd "D:\work folder\kevino\audio-ai"
venv\Scripts\activate
pip install requests
```

### 2. Run Complete Test Suite

```bash
# Test everything
python test_vps_complete.py data/raw/test_audio.wav
```

This will:
- ✅ Test health endpoint
- ✅ Test API info
- ✅ Upload audio file
- ✅ Wait for processing
- ✅ Download report
- ✅ Verify report structure

---

## Step-by-Step Verification

### Step 1: Basic Connectivity

```bash
# Test health
curl http://78.46.37.169:8000/health

# Expected: {"status": "healthy"}
```

### Step 2: API Information

```bash
# Get API info
curl http://78.46.37.169:8000/

# Open docs in browser
# http://78.46.37.169:8000/docs
```

### Step 3: Upload Audio for Analysis

```bash
# Upload file
curl -X POST "http://78.46.37.169:8000/api/v1/provenance-check" \
  -F "file=@test_audio.wav"

# Response: {"job_id": "...", "status": "processing"}
```

### Step 4: Check Processing Status

```bash
# Replace JOB_ID with actual job_id from upload
curl http://78.46.37.169:8000/api/v1/status/JOB_ID

# Wait until status is "completed"
```

### Step 5: Download Provenance Report

```bash
# Download report
curl http://78.46.37.169:8000/api/v1/reports/JOB_ID > report.json

# Inspect report
python inspect_report.py report.json
```

---

## Automated Testing

### Complete Test Suite

```bash
# Run all tests
python test_vps_complete.py test_audio.wav
```

**What it tests:**
1. ✅ Health endpoint
2. ✅ API information
3. ✅ File upload
4. ✅ Processing status
5. ✅ Report download
6. ✅ Report structure validation

### Inspect Report

```bash
# Inspect downloaded report
python inspect_report.py test_reports/report_JOB_ID.json
```

**What it shows:**
- Basic information (file ID, timestamp)
- Summary (segments, risk level, AI probability)
- Segment analysis (per-segment AI probabilities)
- Model provenance (embedding model, version, checksum)
- Index provenance (index type, vectors, checksum)
- Evidence files (spectrograms, snippets)
- Structure validation

---

## Verification Checklist

### ✅ Basic Functionality

- [ ] Health endpoint responds
- [ ] API docs accessible
- [ ] File upload works
- [ ] Processing completes
- [ ] Report downloads successfully

### ✅ Report Structure

- [ ] Report has `file_id`
- [ ] Report has `timestamp`
- [ ] Report has `summary` with:
  - `total_segments`
  - `risk_level`
  - `ai_probability`
- [ ] Report has `segments` array
- [ ] Each segment has:
  - `segment_id`
  - `start` and `end` times
  - `ai_probability`
  - `matches` (if any)
- [ ] Report has `model_provenance`:
  - `model_name`
  - `model_version`
  - `model_checksum`
- [ ] Report has `index_provenance`:
  - `index_type`
  - `total_vectors`
  - `index_checksum`

### ✅ Per-Segment Analysis

- [ ] Each segment has AI probability
- [ ] Segments are analyzed per-stem (vocals, drums, bass, other)
- [ ] Similarity matches are included
- [ ] Match scores are reasonable (0.0-1.0)

### ✅ Forensic Evidence

- [ ] Evidence paths are included
- [ ] Spectrograms are referenced
- [ ] Audio snippets are referenced
- [ ] Match snippets are referenced

### ✅ Model/Index Provenance

- [ ] Model name and version are specified
- [ ] Model checksum is provided
- [ ] Index type and size are specified
- [ ] Index checksum is provided

---

## Face-to-Face Demo Checklist

### 1. Show Repository

```bash
# Show code provenance
git log -1 --format="%H %s"
```

### 2. Run Demo End-to-End

```bash
# Upload test file
python test_vps_complete.py test_audio.wav
```

### 3. Open and Inspect Report

```bash
# Show report structure
python inspect_report.py test_reports/report_*.json
```

### 4. Point to Key Elements

- Show a sample segment
- Show its AI probability
- Show top match similarity
- Show model/index provenance

### 5. Play Evidence (if available)

- Play probe snippet
- Play matched snippet
- Show spectrograms

### 6. Robustness Test (optional)

```bash
# Test with transformed audio
python test_robustness.py test_audio.wav
```

---

## Expected Results

### Successful Test Output

```
======================================================================
VPS COMPLETE TEST SUITE
======================================================================
   VPS URL: http://78.46.37.169:8000
   Testing from: D:\work folder\kevino\audio-ai

======================================================================
TEST 1: Health Check
======================================================================
✅ Health check passed
   Response: {'status': 'healthy'}

======================================================================
TEST 2: API Information
======================================================================
✅ Root endpoint OK
   API: Audio Provenance API v2.0
   Status: running
✅ API documentation available
   Open in browser: http://78.46.37.169:8000/docs

======================================================================
TEST 3: Upload Audio File
======================================================================
   File: test_audio.wav
   Size: 1.23 MB
   Uploading...
✅ Upload successful
   Job ID: abc123-def456-...
   Status: processing

======================================================================
TEST 4: Processing Status
======================================================================
   Job ID: abc123-def456-...
   Waiting for processing (max 300s)...
   Status: processing
   Still processing... (5.2s elapsed)
   Status: completed
✅ Processing completed in 12.3s

======================================================================
TEST 5: Download Provenance Report
======================================================================
✅ Report downloaded
   Saved to: test_reports/report_abc123.json

======================================================================
TEST 6: Verify Report Structure
======================================================================
✅ All required fields present
   Total segments: 10
   Risk level: low
   AI probability: 0.123
   First segment ID: test_audio_seg_0000
   First segment AI prob: 0.150
   Top match similarity: 0.856
   Embedding model: m-a-p/MERT-v1-330M
   Model version: v1.0
   Index type: IndexFlatL2
   Index vectors: 100

======================================================================
TEST SUMMARY
======================================================================
   Total Tests: 6
✅ Passed: 6
❌ Failed: 0

======================================================================
DETAILED RESULTS:
======================================================================
  ✅ PASS - Health Check
  ✅ PASS - API Information
  ✅ PASS - File Upload
  ✅ PASS - Processing
  ✅ PASS - Report Download
  ✅ PASS - Report Structure

======================================================================
✅ ALL TESTS PASSED - System is working correctly!
```

---

## Troubleshooting

### Connection Issues

```bash
# Test connectivity
ping 78.46.37.169

# Test port
telnet 78.46.37.169 8000
```

### Processing Timeout

- Increase `MAX_WAIT` in `test_vps_complete.py`
- Check VPS logs for errors
- Verify VPS has enough resources

### Report Missing Fields

- Check VPS logs for processing errors
- Verify pipeline is complete
- Check report structure matches requirements

---

## Next Steps

1. **Run complete test suite** - Verify all functionality
2. **Inspect reports** - Validate structure and content
3. **Test robustness** - Try different audio formats
4. **Prepare demo** - Use checklist for face-to-face verification

---

**Ready to verify!** Run `python test_vps_complete.py test_audio.wav` to start.

