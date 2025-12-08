# -*- mode: python ; coding: utf-8 -*-
import os
import platform

# Import APP from PyInstaller for macOS app bundle creation
try:
    from PyInstaller.building.api import APP
except ImportError:
    # Fallback for older PyInstaller versions
    try:
        from PyInstaller.building.build_main import APP
    except ImportError:
        APP = None

try:
    spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
except NameError:
    import sys
    if hasattr(sys, '_MEIPASS'):
        spec_dir = os.path.dirname(sys.executable)
    else:
        spec_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

# Find icon file - try multiple locations and formats (cross-platform)
icon_path = None
system = platform.system()

# Determine icon extension based on platform (prefer platform-specific, fallback to other)
icon_ext = '.icns' if system == 'Darwin' else '.ico'
possible_paths = [
    # Platform-specific icon first
    os.path.abspath(os.path.join(spec_dir, f'icon{icon_ext}')),
    # Fallback to other formats
    os.path.abspath(os.path.join(spec_dir, 'icon.ico')),
    os.path.abspath(os.path.join(spec_dir, 'icon.icns')),
    # Current working directory
    os.path.abspath(f'icon{icon_ext}'),
    os.path.abspath('icon.ico'),
    os.path.abspath('icon.icns'),
    os.path.join(os.getcwd(), f'icon{icon_ext}'),
    os.path.join(os.getcwd(), 'icon.ico'),
    os.path.join(os.getcwd(), 'icon.icns'),
]

for path in possible_paths:
    if os.path.exists(path):
        icon_path = os.path.abspath(path)
        break

# Also include both icon files in datas for runtime access
icon_datas = []
if icon_path and os.path.exists(icon_path):
    icon_datas.append((icon_path, '.'))
# Also include the other icon format if it exists
other_icon_ext = '.icns' if icon_ext == '.ico' else '.ico'
other_icon_paths = [
    os.path.abspath(os.path.join(spec_dir, f'icon{other_icon_ext}')),
    os.path.abspath(f'icon{other_icon_ext}'),
    os.path.join(os.getcwd(), f'icon{other_icon_ext}'),
]
for path in other_icon_paths:
    if os.path.exists(path) and path != icon_path:
        icon_datas.append((path, '.'))
        break

# Debug output during build
if 'SPECPATH' in globals() or '__file__' in globals():
    if icon_path:
        print(f"[PyInstaller] Icon path: {icon_path}")
        print(f"[PyInstaller] Icon exists: {os.path.exists(icon_path)}")
        print(f"[PyInstaller] Platform: {system}")
        if len(icon_datas) > 1:
            print(f"[PyInstaller] Including both icon formats for cross-platform support")
    else:
        print(f"[PyInstaller] WARNING: icon file not found! Icon will not be embedded.")
        print(f"[PyInstaller] Searched in: {possible_paths}")

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=[],
    datas=icon_datas,  # Include icon files in bundle for runtime access
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
    [],
    exclude_binaries=True,  # Changed: exclude binaries from EXE
    name='AudioProvenanceGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # Windowed mode
    icon=icon_path,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='AudioProvenanceGUI',
)

# On macOS, wrap COLLECT in APP to create .app bundle
if system == 'Darwin' and APP is not None:
    app = APP(
        coll,
        name='AudioProvenanceGUI',
        icon=icon_path,
        info_plist={
            'NSPrincipalClass': 'NSApplication',
            'NSHighResolutionCapable': 'True',
        },
    )
