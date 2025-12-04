# Troubleshooting Timeout Errors

## Error: "Read timed out"

This error occurs when the connection takes longer than the timeout period.

## Solutions

### 1. Increased Timeouts (Already Applied)

I've increased the timeouts in both test scripts:
- **Connection timeout**: 10 seconds (for health checks)
- **Upload/Processing timeout**: 120 seconds (2 minutes)
- **Max wait time**: 600 seconds (10 minutes)

### 2. Check VPS Status

**On VPS, verify API is running:**
```bash
# Check if uvicorn is running
ps aux | grep uvicorn

# Check if port 8000 is listening
netstat -tlnp | grep 8000
# or
ss -tlnp | grep 8000

# Test from VPS itself
curl http://localhost:8000/health
```

### 3. Check Firewall

**On VPS:**
```bash
# Check firewall status
sudo ufw status

# Allow port 8000 if not already allowed
sudo ufw allow 8000/tcp
sudo ufw reload
```

### 4. Check Network Connectivity

**From local machine:**
```bash
# Test basic connectivity
ping 78.46.37.169

# Test port connectivity
telnet 78.46.37.169 8000
# or
curl -v http://78.46.37.169:8000/health --max-time 10
```

### 5. Processing Takes Too Long

If processing is taking longer than expected:

**Check VPS resources:**
```bash
# Check CPU usage
top

# Check memory
free -h

# Check disk space
df -h
```

**Check VPS logs:**
```bash
# If using systemd service
sudo journalctl -u audio-provenance -f

# If running manually, check terminal output
```

### 6. Large File Uploads

For large files, the upload itself may timeout. The GUI app now uses streaming uploads.

**Try smaller test file first:**
```bash
# Create a small test file
python scripts/create_test_audio.py
```

### 7. Restart API Server

**On VPS:**
```bash
# Stop current server (Ctrl+C if running in terminal)
# Or if using systemd:
sudo systemctl restart audio-provenance

# Start again
cd ~/audio-ai
source venv/bin/activate
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

## Quick Diagnostic Commands

### From Local Machine:
```bash
# 1. Test basic connectivity
ping 78.46.37.169

# 2. Test port
curl -v http://78.46.37.169:8000/health --max-time 10

# 3. Test with longer timeout
curl http://78.46.37.169:8000/health --max-time 30
```

### From VPS:
```bash
# 1. Check API is running
ps aux | grep uvicorn

# 2. Test locally
curl http://localhost:8000/health

# 3. Check logs
tail -f logs/api.log  # if logging to file
```

## Common Causes

1. **API not running** - Most common cause
2. **Firewall blocking** - Port 8000 not open
3. **Network issues** - Connection problems
4. **Processing too slow** - VPS resources insufficient
5. **Large files** - Upload timeout

## Updated Timeouts

The following timeouts have been increased:

- **GUI App**: 
  - Connection: 10s
  - Upload/Processing: 120s
  - Max wait: 600s

- **Test Script**:
  - Connection: 10s
  - Upload/Processing: 120s
  - Max wait: 600s

These should handle most cases. If you still get timeouts, check the VPS status and resources.

