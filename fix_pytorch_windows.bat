@echo off
REM Fix PyTorch DLL error on Windows
echo ============================================================
echo Fixing PyTorch Installation on Windows
echo ============================================================
echo.

cd /d "D:\work folder\kevino\audio-ai"

echo [1/4] Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Virtual environment not found!
    echo Please create venv first: python -m venv venv
    pause
    exit /b 1
)

echo [2/4] Uninstalling old PyTorch...
pip uninstall -y torch torchaudio torchvision
if errorlevel 1 (
    echo Warning: Some packages may not have been installed
)

echo [3/4] Installing PyTorch CPU version (recommended for Windows)...
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
    echo.
    echo ERROR: Failed to install PyTorch
    echo.
    echo Alternative: Install from PyPI
    pip install torch torchaudio
    pause
    exit /b 1
)

echo [4/4] Testing PyTorch installation...
python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
if errorlevel 1 (
    echo.
    echo ERROR: PyTorch still not working
    echo.
    echo Try installing Visual C++ Redistributables:
    echo https://aka.ms/vs/17/release/vc_redist.x64.exe
    pause
    exit /b 1
)

echo.
echo ============================================================
echo PyTorch installation fixed!
echo ============================================================
echo.
echo You can now run:
echo   python scripts\milestone1_demo.py
echo.
pause

