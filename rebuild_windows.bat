@echo off
echo Building Egg Farm Management System...

REM Clean previous build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist EggFarmManagement.spec del /q EggFarmManagement.spec

REM Run PyInstaller
pyinstaller --noconfirm --onedir --windowed --name "EggFarmManagement" ^
    --add-data "egg_farm_system/styles.qss;egg_farm_system" ^
    --add-data "egg_farm_system/assets;egg_farm_system/assets" ^
    --hidden-import "egg_farm_system.database.models" ^
    --hidden-import "egg_farm_system.database.migrate_sales_table" ^
    --hidden-import "egg_farm_system.database.migrate_payment_method" ^
    --hidden-import "egg_farm_system.database.migrate_raw_materials_avg_cost" ^
    run.py

echo.
if errorlevel 1 (
    echo Build Failed!
) else (
    echo Build Successful! Executable is in dist\EggFarmManagement\EggFarmManagement.exe
)
pause
