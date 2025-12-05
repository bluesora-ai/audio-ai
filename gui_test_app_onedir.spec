# -*- mode: python ; coding: utf-8 -*-
# Onedir mode - more reliable for DLLs on Windows
import sys
import os

# Get Python DLL path
python_dll = None
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
            python_dll = (path, '.')  # Place in _internal folder
            print(f"Found Python DLL: {path}")
            break

# Collect binaries
binaries_list = []
if python_dll:
    binaries_list.append(python_dll)

# Also include VCRUNTIME DLLs
if sys.platform == 'win32':
    vcruntime_dlls = ['vcruntime140.dll', 'vcruntime140_1.dll', 'msvcp140.dll']
    for dll_name in vcruntime_dlls:
        dll_path = os.path.join(sys.exec_prefix, 'DLLs', dll_name)
        if os.path.exists(dll_path):
            binaries_list.append((dll_path, '.'))
        else:
            dll_path = os.path.join(os.path.dirname(sys.executable), dll_name)
            if os.path.exists(dll_path):
                binaries_list.append((dll_path, '.'))

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
    [],
    exclude_binaries=True,  # Binaries go in the folder, not in exe
    name='gui_test_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,  # All DLLs go in the _internal folder
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='gui_test_app',
)

