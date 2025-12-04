# Quick Local Testing Guide

## Test VPS from Your Local Machine

### Setup (One Time)

```bash
# Install test dependencies
pip install requests
```

### Run Complete Test

```bash
# Test everything
python test_vps_complete.py data/raw/test_audio.wav
```

### Manual Testing

```bash
# 1. Health check
curl http://78.46.37.169:8000/health

# 2. Upload file
curl -X POST "http://78.46.37.169:8000/api/v1/provenance-check" \
  -F "file=@test_audio.wav"

# 3. Check status (replace JOB_ID)
curl http://78.46.37.169:8000/api/v1/status/JOB_ID

# 4. Download report
curl http://78.46.37.169:8000/api/v1/reports/JOB_ID > report.json

# 5. Inspect report
python inspect_report.py report.json
```

### Browser Testing

Open: `http://78.46.37.169:8000/docs`

Use the interactive API documentation to test all endpoints.

---

## What Gets Tested

✅ **Health & Connectivity** - API is running  
✅ **File Upload** - Audio files can be uploaded  
✅ **Processing** - Background processing works  
✅ **Report Generation** - Provenance reports are created  
✅ **Report Structure** - All required fields are present  
✅ **Model Provenance** - Model info is included  
✅ **Index Provenance** - Index info is included  
✅ **Per-Segment Analysis** - Each segment has AI probability  
✅ **Matches** - Similarity matches are found  

---

## Expected Results

- All tests pass ✅
- Report downloaded to `test_reports/`
- Report structure validated
- All required fields present

---

**See `LOCAL_VERIFICATION_GUIDE.md` for detailed instructions!**

