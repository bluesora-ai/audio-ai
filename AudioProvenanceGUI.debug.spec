# -*- mode: python ; coding: utf-8 -*-
# DEBUG VERSION - Enables console to see errors
# Use this to debug: python3 -m PyInstaller AudioProvenanceGUI.debug.spec --clean --noconfirm
# Once fixed, rebuild with the regular spec file

import os
import platform
import sys

try:
    spec_dir = os.path.dirname(os.path.abspath(SPECPATH))
except NameError:
    if hasattr(sys, '_MEIPASS'):
        spec_dir = os.path.dirname(sys.executable)
    else:
        spec_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()

# Find icon file
icon_path = None
system = platform.system()
icon_ext = '.icns' if system == 'Darwin' else '.ico'
possible_paths = [
    os.path.abspath(os.path.join(spec_dir, f'icon{icon_ext}')),
    os.path.abspath(os.path.join(spec_dir, 'icon.ico')),
    os.path.abspath(os.path.join(spec_dir, 'icon.icns')),
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

icon_datas = []
if icon_path and os.path.exists(icon_path):
    icon_datas.append((icon_path, '.'))

a = Analysis(
    ['run_gui.py'],
    pathex=[],
    binaries=[],
    datas=icon_datas,
    hiddenimports=[
        # Tkinter modules
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.scrolledtext',
        # Third-party packages
        'requests',
        'numpy',
        'matplotlib',
        'matplotlib.backends.backend_tkagg',
        'matplotlib.figure',
        'matplotlib.pyplot',
        'PIL._tkinter_finder',
        # GUI package modules - explicitly include all
        'gui',
        'gui.main',
        'gui.utils',
        'gui.constants',
        'gui.theme',
        'gui.dialogs',
        'gui.api_client',
        'gui.report_display',
        'gui.visualizations',
        'gui.steps',
        'gui.steps.step1_upload',
        'gui.steps.step2_processing',
        'gui.steps.step3_report',
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
    exclude_binaries=True,
    name='AudioProvenanceGUI',
    debug=True,  # Enable debug mode
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,  # ENABLE CONSOLE FOR DEBUGGING
    icon=icon_path,
)

from PyInstaller.building.osx import BUNDLE as APP
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

if sys.platform == 'darwin':
    try:
        coll = APP(
            coll,
            name='AudioProvenanceGUI.app',
            icon=icon_path,
            info_plist={
                'NSPrincipalClass': 'NSApplication',
                'NSHighResolutionCapable': 'True',
            },
        )
    except NameError:
        try:
            from PyInstaller.building.api import APP
            coll = APP(
                coll,
                name='AudioProvenanceGUI',
                icon=icon_path,
                info_plist={
                    'NSPrincipalClass': 'NSApplication',
                    'NSHighResolutionCapable': 'True',
                },
            )
        except ImportError:
            from PyInstaller.building.osx import BUNDLE as APP
            coll = APP(
                coll,
                name='AudioProvenanceGUI',
                icon=icon_path,
                info_plist={
                    'NSPrincipalClass': 'NSApplication',
                    'NSHighResolutionCapable': 'True',
                },
            )

