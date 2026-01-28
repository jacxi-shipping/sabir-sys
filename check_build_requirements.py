"""Check if all requirements for building are met"""
import sys

print("Checking build requirements...")
print(f"Python version: {sys.version}")
print()

# Check PyInstaller
try:
    import PyInstaller
    print("[OK] PyInstaller is installed")
except ImportError:
    print("[X] PyInstaller is NOT installed")
    print("  Install with: pip install pyinstaller")

# Check PySide6
try:
    import PySide6
    print("[OK] PySide6 is installed")
except ImportError:
    print("[X] PySide6 is NOT installed")
    print("  Install with: pip install PySide6")

# Check SQLAlchemy
try:
    import sqlalchemy
    print("[OK] SQLAlchemy is installed")
except ImportError:
    print("[X] SQLAlchemy is NOT installed")
    print("  Install with: pip install sqlalchemy")

print()
print("To install all requirements: pip install -r requirements.txt")

