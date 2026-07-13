#!/bin/bash
echo "======================================================="
echo "Universal Synora Bridge - Isolated Build Environment"
echo "======================================================="
echo ""

if [ ! -d "venv" ]; then
    echo "[1/4] Creating a new isolated virtual environment..."
    python3 -m venv venv
else
    echo "[1/4] Virtual environment already exists."
fi

echo "[2/4] Activating virtual environment..."
source venv/bin/activate

echo "[3/4] Installing/Verifying exact requirements..."
python3 -m pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
pip install pyinstaller

echo ""
echo "[4/4] Starting the Build Script..."
echo ""
python3 build.py

echo ""
echo "Leaving isolated environment..."
deactivate
echo "Done!"
