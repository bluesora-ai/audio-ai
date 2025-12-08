# -*- mode: python ; coding: utf-8 -*-
import os

try:
    spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
except NameError:
    import sys
    if hasattr(sys, '_MEIPASS'):
        spec_dir = os.path.dirname(sys.executable)
    else:
        spec_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

# Find icon.ico file - try multiple locations
icon_path = None
possible_paths = [
    os.path.abspath(os.path.join(spec_dir, 'icon.ico')),  # Next to spec file
    os.path.abspath('icon.ico'),  # Current working directory
    os.path.join(os.getcwd(), 'icon.ico'),  # Explicit current directory
]

for path in possible_paths:
    if os.path.exists(path):
        icon_path = os.path.abspath(path)
        break

# Debug output during build
if 'SPECPATH' in globals() or '__file__' in globals():
    if icon_path:
        print(f"[PyInstaller] Icon path: {icon_path}")
        print(f"[PyInstaller] Icon exists: {os.path.exists(icon_path)}")
    else:
        print(f"[PyInstaller] WARNING: icon.ico not found! Icon will not be embedded.")
        print(f"[PyInstaller] Searched in: {possible_paths}")

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=[],
    datas=[(icon_path, '.')] if icon_path and os.path.exists(icon_path) else [],  # Include icon.ico in bundle for runtime access
    hiddenimports=[],
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
    a.binaries,
    a.datas,
    [],
    name='AudioProvenanceGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX compression - it can corrupt embedded icons
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path,  # Embed icon in exe - must be absolute path
)
