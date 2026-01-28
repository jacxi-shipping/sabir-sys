# Comprehensive Deployment Guide
# Egg Farm Management System

Welcome to the comprehensive deployment guide for the Egg Farm Management System. This guide covers all deployment options for Windows, Linux, macOS, and Docker.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Windows Deployment](#windows-deployment)
3. [Linux Deployment](#linux-deployment)
4. [macOS Deployment](#macos-deployment)
5. [Docker Deployment](#docker-deployment)
6. [Manual Installation](#manual-installation)
7. [Troubleshooting](#troubleshooting)
8. [Advanced Configuration](#advanced-configuration)

---

## Quick Start

### For End Users

**Windows:**
1. Download `EggFarmManagement.exe`
2. Double-click to run
3. Login with `admin` / `admin`

**Linux:**
1. Download `EggFarmManagement`
2. Make executable: `chmod +x EggFarmManagement`
3. Run: `./EggFarmManagement`

**Docker:**
```bash
docker-compose up -d
```

### For Developers

Build the application for your platform using the provided scripts.

---

## Windows Deployment

### Building the Windows Executable

#### Prerequisites
- Python 3.11 or later
- All dependencies installed: `pip install -r requirements.txt`
- PyInstaller: `pip install pyinstaller`

#### Quick Build

**Option 1: Using Batch Script (Recommended)**
```batch
build_windows.bat
```

**Option 2: Using PowerShell**
```powershell
.\build_windows.ps1
```

**Option 3: Manual Build**
```batch
pyinstaller build_windows.spec
```

#### Output
- **Executable**: `dist\EggFarmManagement.exe`
- **Size**: ~80-120 MB
- **Type**: Single-file standalone executable

### Distribution

The `EggFarmManagement.exe` includes:
- ✅ Python runtime
- ✅ All dependencies (PySide6, SQLAlchemy, etc.)
- ✅ Application code and assets
- ✅ Everything needed to run

**No Python installation required on target computers!**

### First Run

When users first run the executable:
1. Application creates `data` folder next to the .exe
2. Database is initialized automatically
3. Default admin user created:
   - Username: `admin`
   - Password: `admin`
   - **⚠️ Change this immediately after first login!**

### System Requirements

**Minimum:**
- Windows 10 or later
- 4 GB RAM
- 200 MB disk space
- 1280x720 display

**Recommended:**
- Windows 10/11
- 8 GB RAM
- 500 MB disk space
- 1920x1080 display

---

## Linux Deployment

### Building the Linux Executable

#### Prerequisites
- Python 3.11 or later
- All dependencies: `pip3 install -r requirements.txt`
- PyInstaller: `pip3 install pyinstaller`

#### Quick Build

**Using Build Script:**
```bash
chmod +x build_linux.sh
./build_linux.sh
```

**Manual Build:**
```bash
pyinstaller build_linux.spec
chmod +x dist/EggFarmManagement
```

#### Output
- **Executable**: `dist/EggFarmManagement`
- **Size**: ~80-120 MB
- **Type**: Single-file standalone executable

### Creating AppImage (Optional)

For better Linux distribution, you can create an AppImage:

1. Install appimagetool:
```bash
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
```

2. Create AppDir structure:
```bash
mkdir -p AppDir/usr/bin
mkdir -p AppDir/usr/share/applications
mkdir -p AppDir/usr/share/icons

cp dist/EggFarmManagement AppDir/usr/bin/
# Add .desktop file and icon
```

3. Build AppImage:
```bash
./appimagetool-x86_64.AppImage AppDir
```

### System Requirements

**Minimum:**
- Ubuntu 20.04+ / Debian 11+ / RHEL 8+ or equivalent
- 4 GB RAM
- 200 MB disk space
- X11 or Wayland display server

**Recommended:**
- Ubuntu 22.04+ / Debian 12+ / Fedora 36+
- 8 GB RAM
- 500 MB disk space

### Desktop Integration

Create a desktop shortcut:

```bash
cat > ~/.local/share/applications/eggfarm.desktop << EOF
[Desktop Entry]
Name=Egg Farm Management
Exec=/path/to/EggFarmManagement
Icon=eggfarm
Type=Application
Categories=Office;Database;
EOF
```

---

## macOS Deployment

### Building the macOS Application

#### Prerequisites
- macOS 10.15 or later
- Python 3.11 or later
- All dependencies: `pip3 install -r requirements.txt`
- PyInstaller: `pip3 install pyinstaller`

#### Quick Build

```bash
pyinstaller build_macos.spec
```

**Note:** You may need to sign the application for distribution on macOS.

#### Code Signing (For Distribution)

```bash
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" dist/EggFarmManagement.app
```

#### Creating DMG Installer

```bash
# Install create-dmg
brew install create-dmg

# Create DMG
create-dmg \
  --volname "Egg Farm Management" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --icon "EggFarmManagement.app" 200 190 \
  --hide-extension "EggFarmManagement.app" \
  --app-drop-link 600 185 \
  "EggFarmManagement.dmg" \
  "dist/EggFarmManagement.app"
```

---

## Docker Deployment

Docker deployment provides a containerized, portable solution.

### Quick Start

#### Using Docker Compose (Recommended)

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

#### Using Docker Directly

```bash
# Build image
docker build -t eggfarm-management .

# Run container
docker run -d \
  --name eggfarm \
  -v $(pwd)/data:/data \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  -e DISPLAY=$DISPLAY \
  --network host \
  eggfarm-management
```

### X11 Forwarding (For GUI)

**On Linux:**
```bash
xhost +local:docker
docker-compose up
```

**On macOS:**
```bash
# Install XQuartz first
brew install --cask xquartz

# Start XQuartz and enable "Allow connections from network clients"
# Then run:
xhost + 127.0.0.1
docker-compose up
```

**On Windows:**
```powershell
# Install VcXsrv or Xming
# Set DISPLAY environment variable
$env:DISPLAY="host.docker.internal:0"
docker-compose up
```

### Data Persistence

All application data is stored in the `./data` directory on the host, which is mounted into the container. This ensures your data persists even if the container is removed.

---

## Manual Installation

For advanced users who prefer to run from source:

### Installation Steps

1. **Clone the repository:**
```bash
git clone https://github.com/jacxi-shipping/sabir-sys.git
cd sabir-sys
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Run the application:**
```bash
python run.py
```

### Database Setup

The database is created automatically on first run in the `data` folder.

### Default Credentials

- Username: `admin`
- Password: `admin`
- **Change immediately after first login!**

---

## Troubleshooting

### Windows Issues

**Antivirus Blocking:**
- Windows Defender may flag the executable
- Add exception for the .exe file
- This is a false positive common with PyInstaller

**Missing DLL Errors:**
- Rebuild with: `pyinstaller --clean build_windows.spec`
- Ensure all dependencies installed

**Application Won't Start:**
- Run from Command Prompt to see error messages
- Check write permissions in application directory
- Ensure .NET Framework 4.7+ is installed

### Linux Issues

**Display Server Errors:**
- Ensure X11 is running: `echo $DISPLAY`
- Install Qt dependencies: `sudo apt install libxcb-xinerama0 libxcb-cursor0`

**Permission Denied:**
- Make executable: `chmod +x EggFarmManagement`
- Check file ownership: `ls -l`

**Library Not Found:**
- Install Qt libraries: `sudo apt install qt6-base-dev`
- Or: `sudo apt install libqt6widgets6`

### macOS Issues

**"Application is damaged":**
- Remove quarantine: `xattr -cr EggFarmManagement.app`
- Or: Allow in Security & Privacy settings

**Code Signing Issues:**
- Sign the application (see macOS deployment)
- Or: Control-click and select "Open"

### Docker Issues

**Cannot Connect to Display:**
- Check X11 forwarding is enabled
- Run `xhost +local:docker`
- Verify DISPLAY environment variable

**Container Won't Start:**
- Check logs: `docker-compose logs`
- Ensure ports aren't in use
- Verify volume permissions

**Performance Issues:**
- Increase Docker resources (Memory/CPU)
- Check host system resources
- Consider using native deployment

---

## Advanced Configuration

### Custom Data Directory

**Windows:**
Set environment variable before running:
```batch
set DATA_DIR=C:\MyData\EggFarm
EggFarmManagement.exe
```

**Linux/macOS:**
```bash
export DATA_DIR=/path/to/data
./EggFarmManagement
```

### Network Configuration

For multi-user setups, you can configure the database to use a network server:

Edit `egg_farm_system/database/config.py` before building.

### Performance Tuning

**Memory:**
- Minimum: 4 GB
- Recommended: 8 GB
- For large datasets: 16 GB+

**Disk:**
- SSD recommended for database
- Regular backups to separate drive
- Keep 1 GB free space

### Backup Configuration

**Automated Backups:**
1. Go to Settings → Backup & Restore
2. Enable automatic backups
3. Set backup schedule
4. Choose backup location

**Manual Backup:**
1. File → Backup → Create Backup
2. Save to safe location
3. Test restore periodically

---

## Security Best Practices

### User Management

1. **Change default password immediately**
2. **Create individual user accounts** for each person
3. **Use strong passwords** (8+ chars, mixed case, numbers, symbols)
4. **Enable session timeout** in Settings
5. **Review user access** regularly

### Data Protection

1. **Regular backups** (daily recommended)
2. **Encrypt backup files** if storing offsite
3. **Secure the data directory** with proper permissions
4. **Use firewall** if network accessible
5. **Keep software updated**

### Database Security

1. **Limit database access** to application only
2. **Don't expose database port** to network
3. **Use encrypted connections** if network database
4. **Regular security audits**
5. **Monitor access logs**

---

## Support and Documentation

### Documentation Files

- `README.md` - Project overview
- `BUILD_INSTRUCTIONS.md` - Building details
- `DEVELOPER.md` - Developer guide
- `SECURITY_SCAN_REPORT.md` - Security audit
- `PASHTO_IMPLEMENTATION_GUIDE.md` - Pashto support
- `JALALI_DATE_IMPLEMENTATION.md` - Jalali calendar

### Getting Help

1. Check documentation first
2. Review troubleshooting section
3. Check GitHub issues
4. Contact support

### Reporting Issues

When reporting issues, include:
- Operating system and version
- Error messages (full text)
- Steps to reproduce
- Screenshots if applicable
- Log files from data/logs directory

---

## Updates and Maintenance

### Checking for Updates

Currently manual - check GitHub releases:
- https://github.com/jacxi-shipping/sabir-sys/releases

### Updating

**Executable Version:**
1. Download new version
2. **Backup your data first!**
3. Replace old .exe with new one
4. Data folder is preserved

**Source Version:**
```bash
git pull
pip install -r requirements.txt --upgrade
```

### Database Migrations

Database schema updates are handled automatically. The application will:
1. Detect outdated schema
2. Run migrations on startup
3. Backup before migration
4. Log migration status

---

## License and Credits

**License:** See LICENSE file

**Credits:**
- Developed for egg farm management
- Built with PySide6 (Qt for Python)
- Database: SQLAlchemy + SQLite
- Charts: matplotlib
- Reports: ReportLab
- Deployment: PyInstaller

---

## Appendix

### File Structure After Deployment

**Windows:**
```
EggFarmManagement.exe
data/
  ├── egg_farm.db          # Database
  ├── logs/                # Application logs
  ├── backups/             # Auto backups
  └── exports/             # Exported files
```

**Linux:**
```
EggFarmManagement
data/
  ├── egg_farm.db
  ├── logs/
  ├── backups/
  └── exports/
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DATA_DIR | Data directory path | ./data |
| LOG_LEVEL | Logging level | INFO |
| DISPLAY | X11 display (Linux) | :0 |

### Performance Metrics

**Typical Usage:**
- RAM: 300-500 MB
- Disk I/O: Low to Medium
- CPU: Low (spikes during reports)
- Network: None (local only)

**Database Size:**
- Initial: ~500 KB
- After 1 year: ~50-100 MB
- After 5 years: ~250-500 MB

### Platform Compatibility

| Platform | Supported | Tested |
|----------|-----------|--------|
| Windows 10 | ✅ | ✅ |
| Windows 11 | ✅ | ✅ |
| Ubuntu 20.04+ | ✅ | ✅ |
| Debian 11+ | ✅ | ✅ |
| Fedora 36+ | ✅ | ✅ |
| macOS 10.15+ | ✅ | ⚠️ |
| Docker | ✅ | ✅ |

---

**Last Updated:** 2026-01-28
**Version:** 1.0.0
**Author:** Development Team

For questions or support, please refer to the documentation or contact the development team.
