# Building Windows Executable - Quick Guide

## Quick Start

1. **Install dependencies** (if not already done):
   ```batch
   pip install -r requirements.txt
   pip install pyinstaller
   ```

2. **Run the build script**:
   ```batch
   build_windows.bat
   ```

3. **Find your executable**:
   - Location: `dist\EggFarmManagement.exe`
   - Size: ~50-100 MB
   - Ready to distribute!

## What Gets Built

The build process creates a **single standalone executable** that includes:
- ✅ All Python code
- ✅ PySide6 (Qt) libraries
- ✅ SQLAlchemy and database drivers
- ✅ All dependencies
- ✅ Stylesheets and assets
- ✅ Everything needed to run the app

## Distribution

**You can copy `EggFarmManagement.exe` to any Windows computer and run it directly** - no Python installation needed!

### First Run Behavior

When users first run the executable:
1. The app creates a `data` folder next to the .exe
2. Database is automatically initialized
3. Default admin user is created:
   - Username: `admin`
   - Password: `admin`
   - **Important**: Change this password after first login!

## Troubleshooting

### Build Fails
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Try: `pip install --upgrade pyinstaller`

### Executable Doesn't Start
- Check Windows Defender/Antivirus (may need to allow the file)
- Run from command prompt to see error messages
- Ensure the .exe has write permissions in its folder

### Missing Files Error
- Rebuild using the spec file: `pyinstaller build_windows.spec`
- Check that `styles.qss` exists in `egg_farm_system/` folder

## Advanced Options

Edit `build_windows.spec` to customize:
- **Executable name**: Change `name='EggFarmManagement'`
- **Add icon**: Set `icon='path/to/icon.ico'`
- **Include more files**: Add to `datas` list

## File Structure After Build

```
dist/
  └── EggFarmManagement.exe  ← This is what you distribute!

build/  ← Can be deleted after build
EggFarmManagement.spec  ← Auto-generated, can be deleted
```

## Notes

- The executable is **portable** - users can run it from anywhere
- Data files (database, logs) are created next to the .exe
- No installation required - just double-click and run!

