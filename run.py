import sys
from pathlib import Path

# Add the current directory to sys.path to ensure egg_farm_system is importable
# This is critical for PyInstaller to resolve the package correctly
sys.path.insert(0, str(Path(__file__).parent.absolute()))

from egg_farm_system.app import main

if __name__ == "__main__":
    main()
