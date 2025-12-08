@echo off
REM Build script for Windows - Local Development
echo === Building AudioProvenanceGUI for Windows ===
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo Virtual environment created.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade PyInstaller
echo Installing/upgrading PyInstaller...
pip install --upgrade pyinstaller

REM Check for icon files
if exist "icon.ico" (
    echo Found icon.ico
) else (
    echo Warning: icon.ico not found! The app will build without an icon.
)

if exist "icon.icns" (
    echo Found icon.icns (for cross-platform support)
)

REM Clean previous builds
echo Cleaning previous builds...
if exist "build" rmdir /s /q build
if exist "dist\AudioProvenanceGUI.exe" del /q "dist\AudioProvenanceGUI.exe"

REM Build the application
echo.
echo Building application...
pyinstaller AudioProvenanceGUI.spec --clean --noconfirm

REM Check if build was successful
if exist "dist\AudioProvenanceGUI.exe" (
    echo.
    echo === Build Complete! ===
    echo Executable: dist\AudioProvenanceGUI.exe
    echo.
    echo You can now run: dist\AudioProvenanceGUI.exe
) else (
    echo.
    echo === Build Failed! ===
    echo Check the error messages above.
    exit /b 1
)

pause

