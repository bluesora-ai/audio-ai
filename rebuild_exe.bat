@echo off
echo ========================================
echo Rebuilding gui_test_app.exe
echo ========================================
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build (
    echo Removing build folder...
    rmdir /s /q build
)
if exist dist (
    echo Removing dist folder...
    rmdir /s /q dist
)

echo.
echo Installing/updating PyInstaller...
pip install --upgrade pyinstaller

echo.
echo ========================================
echo Building executable (this may take a few minutes)...
echo ========================================
echo.
echo Using onedir mode (more reliable for DLLs)...
pyinstaller gui_test_app_onedir.spec --clean
echo.
echo If onedir doesn't work, try onefile mode:
echo   pyinstaller gui_test_app.spec --clean

echo.
echo ========================================
if exist dist\gui_test_app.exe (
    echo SUCCESS! Executable created: dist\gui_test_app.exe
    echo.
    echo File size:
    dir dist\gui_test_app.exe
) else (
    echo ERROR: Build failed! Check the output above for errors.
)
echo ========================================
pause
