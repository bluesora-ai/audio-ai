# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import shutil

# Get Python DLL path and copy it to ensure it's available
python_dll = None
python_dll_dest = None
if sys.platform == 'win32':
    python_version = f"{sys.version_info.major}{sys.version_info.minor}"
    python_dll_name = f"python{python_version}.dll"
    
    # Try to find Python DLL in common locations
    possible_paths = [
        os.path.join(sys.exec_prefix, python_dll_name),
        os.path.join(sys.exec_prefix, 'DLLs', python_dll_name),
        os.path.join(os.path.dirname(sys.executable), python_dll_name),
        os.path.join(os.path.dirname(sys.executable), 'DLLs', python_dll_name),
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            python_dll = path
            # For onedir mode, DLL should be in the same directory as exe
            python_dll_dest = '.'  # Place in _internal folder (onedir) or root (onefile)
            break

# Collect all Python DLLs and dependencies
binaries_list = []
if python_dll:
    binaries_list.append((python_dll, python_dll_dest))
    print(f"Found Python DLL: {python_dll}")

# Also include VCRUNTIME DLLs which Python depends on
if sys.platform == 'win32':
    vcruntime_dlls = ['vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll']
    for dll_name in vcruntime_dlls:
        dll_path = os.path.join(sys.exec_prefix, 'DLLs', dll_name)
        if os.path.exists(dll_path):
            binaries_list.append((dll_path, python_dll_dest))
        else:
            # Try in Python root
            dll_path = os.path.join(os.path.dirname(sys.executable), dll_name)
            if os.path.exists(dll_path):
                binaries_list.append((dll_path, python_dll_dest))

a = Analysis(
    ['gui_test_app.py'],
    pathex=[],
    binaries=binaries_list,
    datas=[
        ('icon.ico', '.'),
    ],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'tkinter.scrolledtext',
        'PIL',
        'PIL.Image',
        'PIL.ImageDraw',
        'PIL.ImageTk',
        'requests',
        'json',
        'threading',
        'pathlib',
        'numpy',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # Include all binaries (Python DLL, etc.) in exe
    a.zipfiles,
    a.datas,
    [],
    name='gui_test_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid DLL issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
    onefile=True,  # Single executable - DLLs will be extracted to temp folder on run
)
