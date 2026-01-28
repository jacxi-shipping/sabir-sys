# Quick Deployment Guide

This guide provides quick instructions for deploying the Egg Farm Management System.

## 🚀 Quick Start

### For End Users (Pre-built Executables)

#### Windows
1. Download `EggFarmManagement.exe`
2. Double-click to run
3. Login: `admin` / `admin`

#### Linux
1. Download `EggFarmManagement`
2. Make executable: `chmod +x EggFarmManagement`
3. Run: `./EggFarmManagement`

### For Developers (Building from Source)

#### One-Command Deployment
```bash
./deploy.sh
```

This automatically:
- Detects your platform
- Installs dependencies
- Builds the executable
- Creates standalone distribution

---

## 📦 Platform-Specific Builds

### Windows

**Quick Build:**
```batch
build_windows.bat
```

**Output:** `dist\EggFarmManagement.exe` (~100 MB)

### Linux

**Quick Build:**
```bash
./build_linux.sh
```

**Output:** `dist/EggFarmManagement` (~100 MB)

### macOS

**Quick Build:**
```bash
pyinstaller build_macos.spec
```

**Output:** `dist/EggFarmManagement.app`

---

## 🐳 Docker Deployment

**Easiest Option for Cross-Platform:**

```bash
# Start the application
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

**Requirements:**
- Docker installed
- X11 server running (for GUI)

---

## 📋 Build Requirements

### All Platforms
- Python 3.11+
- All dependencies: `pip install -r requirements.txt`
- PyInstaller: `pip install pyinstaller`

### Windows
- Windows 10 or later
- No additional requirements

### Linux
- Ubuntu 20.04+ / Debian 11+ / Fedora 36+ or equivalent
- X11 development libraries:
  ```bash
  sudo apt install libxcb-xinerama0 libxcb-cursor0 qt6-base-dev
  ```

### macOS
- macOS 10.15 or later
- Xcode Command Line Tools
- Homebrew (recommended)

---

## 🎯 Deployment Options Summary

| Method | Best For | Complexity | Distribution |
|--------|----------|------------|--------------|
| **PyInstaller** | Desktop deployment | Low | Standalone .exe/.bin |
| **Docker** | Server/Multi-platform | Medium | Container image |
| **Source Install** | Development | Low | Python required |
| **AppImage** (Linux) | Easy Linux dist | Medium | Single file |

---

## 📖 Detailed Documentation

For complete deployment instructions, see:
- **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** - Comprehensive guide
- **[BUILD_INSTRUCTIONS.md](BUILD_INSTRUCTIONS.md)** - Build details
- **[README_BUILD.md](README_BUILD.md)** - Quick build reference

---

## ⚡ Quick Commands Cheat Sheet

```bash
# Build for current platform
./deploy.sh

# Build Windows (on Windows)
build_windows.bat

# Build Linux
./build_linux.sh

# Docker deployment
docker-compose up -d

# Source installation
pip install -r requirements.txt
python run.py

# Clean build artifacts
rm -rf build dist *.spec
```

---

## 🔧 Post-Deployment

After deploying:

1. **Test the executable**
   - Run on target platform
   - Test all major features
   - Check database creation

2. **Security**
   - Change default admin password
   - Review user permissions
   - Enable session timeout

3. **Backup**
   - Set up automatic backups
   - Test restore procedure
   - Document backup location

4. **Documentation**
   - Provide user manual
   - Include troubleshooting guide
   - Share deployment guide

---

## ❓ Troubleshooting

### Build Fails
```bash
# Clean and retry
rm -rf build dist *.spec
pip install --upgrade pyinstaller
./deploy.sh
```

### Executable Won't Run
- Check antivirus settings
- Verify file permissions
- Run from terminal to see errors

### Missing Dependencies
```bash
pip install -r requirements.txt --upgrade
```

### Docker Issues
```bash
# Allow X11 connections
xhost +local:docker

# Rebuild image
docker-compose build --no-cache
```

---

## 📞 Support

For help with deployment:
1. Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)
2. Review [Troubleshooting](#troubleshooting) section
3. Check logs in `data/logs/`
4. Contact development team

---

## ✅ Deployment Checklist

Before distributing:

- [ ] Build successful on target platform
- [ ] Tested on clean system (no Python)
- [ ] Default credentials work
- [ ] Database initializes correctly
- [ ] All features functional
- [ ] Documentation included
- [ ] License file included
- [ ] Version number updated
- [ ] Release notes written
- [ ] Security scan passed

---

**Last Updated:** 2026-01-28  
**Version:** 1.0.0

For the most up-to-date information, see [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).
