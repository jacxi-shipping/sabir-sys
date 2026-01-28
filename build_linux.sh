#!/bin/bash
# Build script for Linux executable
# This script builds the Egg Farm Management System as a standalone Linux executable

set -e  # Exit on error

echo "========================================"
echo "Building Egg Farm Management System"
echo "========================================"
echo ""

# Check if PyInstaller is installed
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "PyInstaller not found. Installing..."
    pip3 install pyinstaller
fi

echo ""
echo "Cleaning previous build..."
rm -rf build dist *.spec

echo ""
echo "Building Linux executable..."
pyinstaller build_linux.spec

if [ $? -ne 0 ]; then
    echo ""
    echo "Build failed!"
    exit 1
fi

echo ""
echo "Making executable..."
chmod +x dist/EggFarmManagement

echo ""
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo ""
echo "The executable is located at: dist/EggFarmManagement"
echo ""
echo "You can now distribute this file to other Linux computers."
echo ""
