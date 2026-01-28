# 🚀 Quick Deploy - Egg Farm Management System

## For Users - Just Run It!

### Windows
1. Download: `EggFarmManagement.exe`
2. Double-click to run
3. Login: `admin` / `admin`
4. **That's it!** No Python needed.

### Linux
1. Download: `EggFarmManagement`
2. Open terminal in download folder
3. Run: `chmod +x EggFarmManagement && ./EggFarmManagement`
4. Login: `admin` / `admin`

### Docker
1. Install Docker
2. Run: `docker-compose up -d`
3. Access the application

---

## For Developers - Build It!

### One Command (Auto-Detects Platform)
```bash
./deploy.sh
```

Done! Find your executable in `dist/` folder.

---

## Platform-Specific Builds

### Windows
```batch
build_windows.bat
```
**Output:** `dist\EggFarmManagement.exe`

### Linux
```bash
./build_linux.sh
```
**Output:** `dist/EggFarmManagement`

### Docker
```bash
docker-compose build
docker-compose up -d
```

---

## What You Get

✅ **Standalone executable** (~100 MB)  
✅ **No Python required** on target computer  
✅ **No dependencies** to install  
✅ **Just works** - download and run!  

---

## Need Help?

📖 **Complete guides:**
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - Comprehensive manual
- [DEPLOY.md](DEPLOY.md) - Quick reference
- [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) - Overview

🐛 **Troubleshooting:**
- Windows: Allow in antivirus
- Linux: Install `libxcb-xinerama0`
- macOS: `xattr -cr EggFarmManagement.app`

---

## 🎯 That's It!

**Build:** `./deploy.sh`  
**Test:** `./dist/EggFarmManagement`  
**Distribute:** Share the executable!

**Ready to deploy on any platform!** 🎉
