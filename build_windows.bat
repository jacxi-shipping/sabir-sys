@echo off
REM Build script for Windows executable
REM This script builds the Egg Farm Management System as a standalone Windows executable

echo ========================================
echo Building Egg Farm Management System
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller
        pause
        exit /b 1
    )
)

echo.
echo Cleaning previous build...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist EggFarmManagement.spec del /q EggFarmManagement.spec

echo.
echo Building Windows executable...
pyinstaller build_windows.spec

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo The executable is located in: dist\EggFarmManagement.exe
echo.
echo You can now distribute this file to other Windows computers.
echo.
pause

