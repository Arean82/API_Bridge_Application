@echo off
echo =======================================================
echo Universal API Bridge - Isolated Build Environment
echo =======================================================
echo.

IF NOT EXIST "venv" (
    echo [1/4] Creating a new isolated virtual environment...
    python -m venv venv
) ELSE (
    echo [1/4] Virtual environment already exists.
)

echo [2/4] Activating virtual environment...
call venv\Scripts\activate.bat

echo [3/4] Installing/Verifying exact requirements...
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
pip install pyinstaller

echo.
echo [4/4] Starting the Build Script...
echo.
python build.py

echo.
echo Leaving isolated environment...
deactivate
echo Done!
pause
