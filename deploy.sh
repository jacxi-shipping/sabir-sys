#!/bin/bash
# Quick deployment script for all platforms
# This script helps you build the application for your current platform

set -e

echo "=============================================="
echo "Egg Farm Management System - Quick Deploy"
echo "=============================================="
echo ""

# Detect platform
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    PLATFORM="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    PLATFORM="macos"
elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
    PLATFORM="windows"
else
    echo "Unsupported platform: $OSTYPE"
    exit 1
fi

echo "Detected platform: $PLATFORM"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "Python version:"
python3 --version
echo ""

# Check dependencies
echo "Checking dependencies..."
if ! python3 -c "import PySide6" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
else
    echo "Dependencies already installed"
fi

# Check PyInstaller
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "Installing PyInstaller..."
    pip3 install pyinstaller
fi

echo ""
echo "Building for $PLATFORM..."
echo ""

# Build based on platform
case $PLATFORM in
    linux)
        if [ -f "build_linux.sh" ]; then
            chmod +x build_linux.sh
            ./build_linux.sh
        else
            pyinstaller build_linux.spec
        fi
        ;;
    macos)
        if [ -f "build_macos.spec" ]; then
            pyinstaller build_macos.spec
        else
            echo "macOS build not configured yet"
            echo "Use: pyinstaller --onefile --windowed --name EggFarmManagement run.py"
        fi
        ;;
    windows)
        if [ -f "build_windows.bat" ]; then
            ./build_windows.bat
        else
            pyinstaller build_windows.spec
        fi
        ;;
esac

echo ""
echo "=============================================="
echo "Build complete!"
echo "=============================================="
echo ""
echo "Executable location: dist/"
echo ""
echo "Next steps:"
echo "1. Test the executable: cd dist && ./EggFarmManagement"
echo "2. Distribute the executable to users"
echo "3. Users can run it without Python installed!"
echo ""
