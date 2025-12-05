#!/usr/bin/env python
"""Check which Python is being used and if matplotlib is available."""
import sys
import os

print("=" * 60)
print("Python Environment Check")
print("=" * 60)
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")
print(f"Python path: {sys.path[:3]}...")  # First 3 entries
print()

# Check matplotlib
print("Checking matplotlib...")
try:
    import matplotlib
    print(f"✓ matplotlib found at: {matplotlib.__file__}")
    print(f"✓ matplotlib version: {matplotlib.__version__}")
    
    # Try to set backend
    matplotlib.use('TkAgg', force=False)
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    print("✓ TkAgg backend available")
    print("✓ All matplotlib components OK")
except ImportError as e:
    print(f"✗ matplotlib ImportError: {e}")
    print(f"  This means matplotlib is NOT installed for this Python")
except Exception as e:
    print(f"✗ matplotlib error: {e}")

print()

# Check requests-toolbelt
print("Checking requests-toolbelt...")
try:
    from requests_toolbelt.multipart.encoder import MultipartEncoder
    print("✓ requests-toolbelt found")
except ImportError as e:
    print(f"✗ requests-toolbelt ImportError: {e}")

print()
print("=" * 60)
print("To fix: Run this command with the SAME Python:")
print(f"  {sys.executable} -m pip install matplotlib requests-toolbelt")
print("=" * 60)

