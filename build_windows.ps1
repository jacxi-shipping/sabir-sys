# PowerShell build script for Windows executable
# This script builds the Egg Farm Management System as a standalone Windows executable

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Building Egg Farm Management System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if PyInstaller is installed
try {
    python -c "import PyInstaller" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller not found"
    }
} catch {
    Write-Host "PyInstaller not found. Installing..." -ForegroundColor Yellow
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to install PyInstaller" -ForegroundColor Red
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host ""
Write-Host "Cleaning previous build..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "EggFarmManagement.spec") { Remove-Item -Force "EggFarmManagement.spec" }

Write-Host ""
Write-Host "Building Windows executable..." -ForegroundColor Green
pyinstaller build_windows.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Build failed!" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Build completed successfully!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "The executable is located in: dist\EggFarmManagement.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "You can now distribute this file to other Windows computers." -ForegroundColor Cyan
Write-Host ""
Read-Host "Press Enter to exit"

