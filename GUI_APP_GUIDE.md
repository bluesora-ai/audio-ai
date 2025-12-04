# GUI Test App Guide

## Quick Start

### Run the GUI App

```bash
# On your local machine
cd "D:\work folder\kevino\audio-ai"
venv\Scripts\activate
python gui_test_app.py
```

## Features

### 1. Test Health
- Click "Test Health" to verify API is running
- Shows connection status

### 2. Upload & Process
- Click "Browse" to select audio file
- Click "Upload & Process" to upload and start processing
- Automatically monitors processing status
- Shows job ID when upload succeeds

### 3. Check Status
- Manually check processing status
- Shows current job status

### 4. Download Report
- Downloads provenance report after processing completes
- Displays report summary in the app
- Saves report to `test_reports/` directory

### 5. Clear
- Clears all logs and resets the interface

## Interface Layout

```
┌─────────────────────────────────────────┐
│   Audio Provenance Test App             │
├─────────────────────────────────────────┤
│ VPS URL: [http://78.46.37.169:8000]    │
│ Audio File: [path] [Browse]             │
├─────────────────────────────────────────┤
│ [Test Health] [Upload] [Status] [Report]│
├─────────────────────────────────────────┤
│ Status: Ready                           │
│ [Progress Bar]                          │
│ Job ID: [auto-filled]                   │
├─────────────────────────────────────────┤
│ Log Output:                             │
│ [Scrollable log area]                   │
├─────────────────────────────────────────┤
│ Report Summary:                         │
│ [Report details]                        │
└─────────────────────────────────────────┘
```

## Usage Workflow

1. **Start App**: `python gui_test_app.py`
2. **Test Connection**: Click "Test Health"
3. **Select File**: Click "Browse" and select audio file
4. **Upload**: Click "Upload & Process"
5. **Wait**: App automatically monitors processing
6. **View Report**: Click "Download Report" when complete
7. **Review**: Check report summary in the app

## What Gets Displayed

### Log Output
- All API calls and responses
- Status updates
- Error messages
- Processing progress

### Report Summary
- File ID and timestamp
- Total segments
- Risk level
- AI/Human probabilities
- Segment details (first 5)
- Model provenance

## Troubleshooting

**App won't start:**
- Make sure Python has tkinter (usually built-in)
- On Linux: `sudo apt install python3-tk`

**Connection errors:**
- Check VPS URL is correct
- Verify API is running on VPS
- Check firewall settings

**Processing fails:**
- Check log output for error details
- Verify audio file format (WAV recommended)
- Check VPS logs

---

**No web browser needed - everything in a desktop app!**

