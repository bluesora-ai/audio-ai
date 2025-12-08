# -*- mode: python ; coding: utf-8 -*-
import os
import platform
import sys

# APP should be automatically available in PyInstaller spec namespace on macOS
# But if it's not, we'll try to import it or access it from the namespace
# Note: PyInstaller injects APP into the spec namespace when executing the spec file
# So we check for it at runtime rather than importing at the top

try:
    spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
except NameError:
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
# APP should be available in the spec namespace automatically on macOS
# PyInstaller injects APP into the spec namespace when executing the spec file
if sys.platform == 'darwin':

    print(f"[PyInstaller] Platform detected: {system} (macOS)")
    print(f"[PyInstaller] Checking for APP class in namespace...")
    print(f"[PyInstaller] 'APP' in globals(): {'APP' in globals()}")
    print(f"[PyInstaller] 'APP' in dir(): {'APP' in dir()}")
    
    # On macOS, PyInstaller makes APP available in the spec namespace
    # Try to use it directly first (most common case)
    try:
        # APP should be in the namespace - use it directly
        print(f"[PyInstaller] Attempting to use APP from namespace...")
        app = APP(
            coll,
            name='AudioProvenanceGUI',
            icon=icon_path,
            info_plist={
                'NSPrincipalClass': 'NSApplication',
                'NSHighResolutionCapable': 'True',
            },
        )

        coll = app

        print(f"[PyInstaller] ✓ Successfully created app bundle using APP from namespace")
    except NameError as e:
        print(f"[PyInstaller] APP not in namespace, trying explicit import...")
        # If APP is not in namespace, import it explicitly
        try:
            from PyInstaller.building.api import APP
            print(f"[PyInstaller] ✓ Imported APP from PyInstaller.building.api")
            app = APP(
                coll,
                name='AudioProvenanceGUI',
                icon=icon_path,
                info_plist={
                    'NSPrincipalClass': 'NSApplication',
                    'NSHighResolutionCapable': 'True',
                },
            )
            print(f"[PyInstaller] ✓ Successfully created app bundle using imported APP")
        except ImportError as import_err:
            print(f"[PyInstaller] Import from api failed, trying alternative path...")
            # Try alternative import path
            try:
                from PyInstaller.building.osx import BUNDLE as APP
                print(f"[PyInstaller] ✓ Imported BUNDLE as APP from PyInstaller.building.osx")
                app = APP(
                    coll,
                    name='AudioProvenanceGUI',
                    icon=icon_path,
                    info_plist={
                        'NSPrincipalClass': 'NSApplication',
                        'NSHighResolutionCapable': 'True',
                    },
                )
                print(f"[PyInstaller] ✓ Successfully created app bundle using BUNDLE")
            except ImportError as final_err:
                # This should never happen on macOS with proper PyInstaller installation
                error_msg = (
                    f"CRITICAL: Failed to create macOS app bundle.\n"
                    f"APP class not found in PyInstaller.\n"
                    f"NameError: {e}\n"
                    f"ImportError (api): {import_err}\n"
                    f"ImportError (osx): {final_err}\n"
                    f"Please ensure PyInstaller is properly installed: pip install --upgrade pyinstaller"
                )
                print(f"[PyInstaller] ✗ {error_msg}")
                raise RuntimeError(error_msg)
