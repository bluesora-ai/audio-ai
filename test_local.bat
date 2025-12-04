@echo off
echo ============================================================
echo LOCAL TESTING - Audio Provenance System
echo ============================================================
echo.

cd /d "D:\work folder\kevino\audio-ai"

echo [1/5] Activating virtual environment...
call venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Virtual environment not found!
    echo Please create venv first: python -m venv venv
    pause
    exit /b 1
)

echo [2/5] Testing imports...
python -c "from src.pipeline import PipelineOrchestrator; print('✓ All imports OK')"
if errorlevel 1 (
    echo ERROR: Import failed! Install dependencies first.
    pause
    exit /b 1
)

echo [3/5] Creating test audio...
python scripts\create_test_audio.py
if errorlevel 1 (
    echo ERROR: Failed to create test audio
    pause
    exit /b 1
)

echo [4/5] Running Milestone 1 demo...
python scripts\milestone1_demo.py
if errorlevel 1 (
    echo ERROR: Demo failed
    pause
    exit /b 1
)

echo [5/5] Checking generated files...
if exist "data\derived\segments\*.wav" (
    echo ✓ Segments created
) else (
    echo ✗ Segments not found
)

if exist "data\embeddings\*.npy" (
    echo ✓ Embeddings created
) else (
    echo ✗ Embeddings not found
)

if exist "data\indexes\faiss_index.bin" (
    echo ✓ FAISS index created
) else (
    echo ✗ FAISS index not found
)

echo.
echo ============================================================
echo LOCAL TESTING COMPLETE
echo ============================================================
echo.
echo To start API server:
echo   uvicorn api.main:app --host 127.0.0.1 --port 8000
echo.
echo To test API:
echo   curl http://localhost:8000/health
echo.
pause

