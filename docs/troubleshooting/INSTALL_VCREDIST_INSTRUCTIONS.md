# Install Visual C++ Redistributables - REQUIRED for OpenL3

## Why This is Needed

OpenL3 requires TensorFlow, which needs Visual C++ Runtime DLLs on Windows. These are **NOT** installed automatically with Python.

## Quick Fix (Choose One Method)

### Method 1: Download and Install (Easiest)

1. **Download:**
   - Click here: [Download Visual C++ Redistributables](https://aka.ms/vs/17/release/vc_redist.x64.exe)
   - Or visit: https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist

2. **Install:**
   - Run the downloaded `vc_redist.x64.exe`
   - Click "Install"
   - Wait for installation to complete

3. **IMPORTANT - Restart:**
   - **Close ALL terminal windows**
   - **Close your IDE/editor**
   - **Restart your terminal/IDE**
   - This is critical - DLLs won't load until restart!

4. **Test:**
   ```bash
   python -c "import tensorflow as tf; print('TensorFlow works!')"
   python -c "import openl3; print('OpenL3 works!')"
   ```

### Method 2: Using winget (if you have it)

Open PowerShell as Administrator and run:

```powershell
winget install Microsoft.VCRedist.2015+.x64
```

Then restart your terminal/IDE.

### Method 3: Using Chocolatey (if you have it)

Open PowerShell as Administrator and run:

```powershell
choco install vcredist-all -y
```

Then restart your terminal/IDE.

## After Installation

1. **Restart your terminal/IDE** (this is essential!)
2. Test TensorFlow:
   ```bash
   python fix_tensorflow_dll.py
   ```
3. If successful, openl3 will automatically work!

## Verification

After installing and restarting, run these commands:

```bash
# Test TensorFlow
python -c "import tensorflow as tf; print('TensorFlow version:', tf.__version__)"

# Test OpenL3
python -c "import openl3; print('OpenL3 imported successfully!')"

# Test your code
python -c "from src.stage3_embedding.embedding_generator import HAS_OPENL3; print('HAS_OPENL3:', HAS_OPENL3)"
```

All should return successfully.

## What You'll See When It Works

Instead of:
```
WARNING - Using fallback embedding (openl3 not available)
```

You'll see:
- No warnings
- OpenL3 embeddings being used
- Full functionality enabled

## If Installation Fails

If you get errors during installation:
1. Make sure you're downloading the **x64** version (64-bit)
2. Try running the installer as Administrator (right-click → Run as Administrator)
3. Check if you already have it installed (Control Panel → Programs)

## Current Status

- ✅ OpenL3: Installed (0.4.2)
- ✅ TensorFlow: Installed (tensorflow-cpu 2.19.0)
- ⚠️ **System DLLs: Need to install** ← DO THIS NOW
- ⚠️ OpenL3: Blocked until DLLs installed

**Action Required:** Install Visual C++ Redistributables and restart!

