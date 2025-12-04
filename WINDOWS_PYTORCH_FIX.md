# Fix PyTorch DLL Error on Windows

## Problem

You're seeing this error:
```
OSError: [WinError 1114] A dynamic link library (DLL) initialization routine failed.
Error loading "C:\Users\...\torch\lib\c10.dll"
```

## Quick Fix

### Option 1: Automated Fix Script

```cmd
REM Run the fix script
fix_pytorch_windows.bat
```

### Option 2: Manual Fix

```cmd
REM 1. Activate venv
cd "D:\work folder\kevino\audio-ai"
venv\Scripts\activate

REM 2. Uninstall old PyTorch
pip uninstall -y torch torchaudio torchvision

REM 3. Install PyTorch CPU version (recommended)
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu

REM 4. Test
python -c "import torch; print('OK')"
```

### Option 3: Install Visual C++ Redistributables

If PyTorch still fails, install:
- **Visual C++ Redistributables**: https://aka.ms/vs/17/release/vc_redist.x64.exe

Then reinstall PyTorch:
```cmd
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## What Changed

I've updated `stem_separator.py` to use **lazy imports** for PyTorch. This means:
- ✅ The module can be imported even if PyTorch fails
- ✅ Stem separation will use fallback mode if PyTorch isn't available
- ✅ Milestone 1 demo will work without PyTorch

## Test After Fix

```cmd
python scripts\milestone1_demo.py
```

Should work now! If PyTorch still fails, the demo will run with fallback mode.

