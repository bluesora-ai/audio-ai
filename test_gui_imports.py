#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Test GUI imports exactly as the GUI script does."""

import sys
print(f"Python: {sys.executable}")
print(f"Version: {sys.version}")
print()

# Test matplotlib exactly as GUI does
HAS_MATPLOTLIB = False
try:
    import matplotlib
    print("✓ matplotlib imported")
    matplotlib.use('TkAgg', force=False)
    print("✓ TkAgg backend set")
    import matplotlib.pyplot as plt
    print("✓ pyplot imported")
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
    print("✓ backend_tkagg imported")
    from matplotlib.figure import Figure
    print("✓ Figure imported")
    import matplotlib.patches as mpatches
    print("✓ patches imported")
    HAS_MATPLOTLIB = True
    print("\n✓✓✓ matplotlib: SUCCESS ✓✓✓")
except ImportError as e:
    print(f"✗✗✗ matplotlib ImportError: {e} ✗✗✗")
except Exception as e:
    print(f"✗✗✗ matplotlib Exception: {e} ✗✗✗")

print()

# Test requests-toolbelt
try:
    from requests_toolbelt.multipart.encoder import MultipartEncoder
    from requests_toolbelt import MultipartEncoderMonitor
    print("✓✓✓ requests-toolbelt: SUCCESS ✓✓✓")
except ImportError as e:
    print(f"✗✗✗ requests-toolbelt ImportError: {e} ✗✗✗")

print()
if HAS_MATPLOTLIB:
    print("=" * 60)
    print("All packages are available!")
    print("If GUI still shows error, try:")
    print("  1. Close and reopen terminal")
    print("  2. Run: python gui_test_app.py")
    print("=" * 60)
else:
    print("=" * 60)
    print("matplotlib is NOT available!")
    print(f"Install with: {sys.executable} -m pip install matplotlib")
    print("=" * 60)

