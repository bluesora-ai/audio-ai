# Testing Tools - Quick Reference

## Files

- **`test_vps_complete.py`** - Complete automated test suite
- **`inspect_report.py`** - Inspect and validate provenance reports
- **`test_remote.py`** - Basic remote API testing
- **`LOCAL_VERIFICATION_GUIDE.md`** - Complete verification guide

## Quick Start

### 1. Install Dependencies

```bash
pip install requests
```

### 2. Run Complete Test

```bash
python test_vps_complete.py test_audio.wav
```

### 3. Inspect Report

```bash
python inspect_report.py test_reports/report_*.json
```

## What Each Tool Does

### `test_vps_complete.py`

**Purpose:** Complete end-to-end testing of VPS deployment

**Usage:**
```bash
python test_vps_complete.py <audio_file.wav>
```

**Tests:**
1. Health endpoint
2. API information
3. File upload
4. Processing status
5. Report download
6. Report structure validation

**Output:**
- Test results with ✅/❌ indicators
- Downloaded reports in `test_reports/`
- Detailed summary

### `inspect_report.py`

**Purpose:** Inspect and validate provenance report structure

**Usage:**
```bash
python inspect_report.py <report.json>
```

**Shows:**
- Basic information
- Summary statistics
- Segment analysis
- Model provenance
- Index provenance
- Evidence files
- Structure validation

### `test_remote.py`

**Purpose:** Basic remote API testing

**Usage:**
```bash
python test_remote.py <audio_file.wav>
```

**Tests:**
- Basic connectivity
- File upload
- Status checking
- Report download

---

## Verification Checklist

Use this checklist to verify all requirements:

- [ ] Health endpoint responds
- [ ] File upload works
- [ ] Processing completes
- [ ] Report downloads successfully
- [ ] Report has all required fields
- [ ] Per-segment analysis present
- [ ] AI probabilities included
- [ ] Similarity matches found
- [ ] Model provenance included
- [ ] Index provenance included
- [ ] Evidence paths included

---

## Troubleshooting

**Connection refused:**
- Check VPS is running
- Check firewall allows port 8000
- Verify API server is started

**Processing timeout:**
- Increase `MAX_WAIT` in test script
- Check VPS resources
- Check VPS logs

**Report missing fields:**
- Check VPS logs for errors
- Verify pipeline completed
- Check report structure

---

**For detailed instructions, see `LOCAL_VERIFICATION_GUIDE.md`**
