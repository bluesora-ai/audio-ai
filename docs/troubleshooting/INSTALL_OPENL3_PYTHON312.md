# Installing OpenL3 on Python 3.12

## Problem
OpenL3 fails to install on Python 3.12 because it uses the `imp` module, which was removed in Python 3.12.

## Solution

The project includes a Python 3.12 compatibility installation script that patches openl3's source code to work with Python 3.12.

### Quick Install

Run the installation script:

```bash
python scripts/install_openl3_python312.py
```

This script will:
1. Clone/download openl3 source code
2. Install imp2importlib compatibility layer  
3. Patch setup.py and other files to replace `imp` module usage
4. Install the patched version

### Manual Installation (If Script Fails)

If the automated script doesn't work, you can install manually:

1. **Install imp2importlib:**
   ```bash
   pip install imp2importlib
   ```

2. **Clone openl3 repository:**
   ```bash
   git clone --depth 1 https://github.com/marl/openl3.git
   cd openl3
   ```

3. **Patch setup.py:**
   Replace `import imp` with:
   ```python
   try:
       import imp2importlib as imp
   except ImportError:
       raise ImportError("imp2importlib is required for Python 3.12+. Install with: pip install imp2importlib")
   ```

4. **Install:**
   ```bash
   pip install . --no-build-isolation
   ```

### Alternative: Use Python 3.11

If installation continues to fail, you can use Python 3.11 where the `imp` module still exists:

```bash
# Create a virtual environment with Python 3.11
python3.11 -m venv venv311
source venv311/bin/activate  # On Windows: venv311\Scripts\activate
pip install -r requirements.txt
```

### Current Status

The installation script (`scripts/install_openl3_python312.py`) is being refined. The codebase has a fallback embedding method that works without openl3, so you can proceed with development while working on the installation.

## Notes

- Model weights will be downloaded automatically on first use of openl3
- The embedding generator has a fallback mode using librosa features if openl3 is not available
- All tests can be run with the fallback embedding method

