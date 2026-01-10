# Building Windows Executable

This guide explains how to build the Egg Farm Management System as a standalone Windows executable (.exe file).

## Prerequisites

1. **Python 3.11 or later** installed on Windows
2. **All dependencies** installed (run `pip install -r requirements.txt`)
3. **PyInstaller** (will be installed automatically by the build script)

## Quick Build

### Option 1: Using Batch Script (Recommended)
```batch
build_windows.bat
```

### Option 2: Using PowerShell Script
```powershell
.\build_windows.ps1
```

### Option 3: Manual Build
```batch
pip install pyinstaller
pyinstaller build_windows.spec
```

## Build Output

After a successful build, you'll find:
- **Executable**: `dist\EggFarmManagement.exe`
- **Build files**: `build\` directory (can be deleted)
- **Spec file**: `EggFarmManagement.spec` (auto-generated, can be deleted)

## Distribution

The `EggFarmManagement.exe` file is a standalone executable that includes:
- All Python dependencies
- PySide6 (Qt) libraries
- SQLAlchemy and database drivers
- All application code
- Stylesheets and assets

**You can distribute this single .exe file to any Windows computer without requiring Python or any dependencies to be installed.**

## File Size

The executable will be approximately **50-100 MB** depending on included libraries.

## First Run

When users run the executable for the first time:
1. The application will create a `data` folder in the same directory as the .exe
2. The database will be automatically initialized
3. Default admin user will be created (username: `admin`, password: `admin`)

## Troubleshooting

### Build Fails
- Ensure all dependencies are installed: `pip install -r requirements.txt`
- Try cleaning and rebuilding: Delete `build` and `dist` folders, then rebuild

### Executable Doesn't Run
- Check Windows Defender/Antivirus - it may flag the executable
- Run from command prompt to see error messages
- Check that the executable has write permissions in its directory

### Missing Files Error
- Ensure `styles.qss` and `assets` folder are in the correct location
- Rebuild with the spec file to include all data files

## Advanced Configuration

To customize the build, edit `build_windows.spec`:
- Change executable name: Edit `name='EggFarmManagement'`
- Add icon: Set `icon='path/to/icon.ico'`
- Include additional files: Add to `datas` list
- Add hidden imports: Add to `hiddenimports` list

## Notes

- The executable is built with `--onefile` option (single file)
- Console is disabled (`console=False`) for a cleaner user experience
- UPX compression is enabled to reduce file size
- All paths are relative to the executable location

