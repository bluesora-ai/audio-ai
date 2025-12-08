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

icon_path = os.path.abspath(os.path.join(spec_dir, 'icon.ico'))

if not os.path.exists(icon_path):
    icon_path = os.path.abspath('icon.ico')

if 'SPECPATH' in globals() or '__file__' in globals():
    print(f"[PyInstaller] Icon path: {icon_path}")
    print(f"[PyInstaller] Icon exists: {os.path.exists(icon_path)}")

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=[],
    datas=[],
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
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_path if os.path.exists(icon_path) else None,
)
