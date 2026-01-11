"""
Configuration file for Egg Farm Management System
"""
import os
import sys
from pathlib import Path

# Application metadata
APP_NAME = "Egg Farm Management System"
APP_VERSION = "1.0.0"
APP_AUTHOR = "Farm Management Team"

# Paths
# Handle both development and PyInstaller executable modes
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    BASE_DIR = Path(sys.executable).parent
else:
    # Running as script
    BASE_DIR = Path(__file__).parent.parent

DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "egg_farm.db"
LOGS_DIR = BASE_DIR / "logs"

# Create necessary directories
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# Database
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Currency settings
BASE_CURRENCY = "AFG"
SECONDARY_CURRENCY = "USD"
DEFAULT_EXCHANGE_RATE = 78.0  # Default AFG to USD rate

# Farm settings
MAX_FARMS = 4

# UI Settings
WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
SIDEBAR_WIDTH = 250

# Expense categories
EXPENSE_CATEGORIES = [
    "Labor",
    "Medicine",
    "Electricity",
    "Water",
    "Transport",
    "Miscellaneous"
]

# Feed types
FEED_TYPES = ["Starter", "Grower", "Layer"]

# Egg grades
EGG_GRADES = ["Small", "Medium", "Large", "Broken"]

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Company/Farm Information for PDF exports
COMPANY_NAME = "Egg Farm Management System"  # Can be customized
COMPANY_ADDRESS = ""  # Can be customized
COMPANY_PHONE = ""  # Can be customized

def get_asset_path(filename: str) -> str:
    """
    Get absolute path for an asset file, handling both dev and PyInstaller frozen modes.
    
    Args:
        filename (str): Name of the asset file (e.g. 'icon_edit.svg')
    
    Returns:
        str: Absolute path to the asset file
    """
    # Base directory resolution
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        base_path = Path(sys.executable).parent
        # Handle PyInstaller 6+ _internal folder
        if (base_path / "_internal").exists():
            base_path = base_path / "_internal"
        
        # In frozen mode, assets are in egg_farm_system/assets relative to base
        asset_dir = base_path / "egg_farm_system" / "assets"
    else:
        # Running as script
        # egg_farm_system/config.py -> egg_farm_system -> parent -> egg_farm_system/assets
        asset_dir = Path(__file__).parent / "assets"
    
    return str(asset_dir / filename)