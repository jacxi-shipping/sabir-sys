"""
Main application entry point
"""
from egg_farm_system.utils.i18n import tr

import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Ensure all models are loaded and registered with SQLAlchemy's Base.metadata early
import egg_farm_system.database.models

from PySide6.QtWidgets import QApplication, QDialog
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.ui.main_window import MainWindow
from egg_farm_system.ui.forms.login_dialog import LoginDialog
from egg_farm_system.config import APP_NAME, APP_VERSION, LOGS_DIR, LOG_LEVEL, LOG_FORMAT
from egg_farm_system.ui.ui_helpers import apply_theme
from egg_farm_system import config as _config

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOGS_DIR / "app.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    try:
        logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName(APP_NAME)
        app.setApplicationVersion(APP_VERSION)
        # Apply consolidated theme (global styles + theme rules)
        try:
            apply_theme(app, getattr(_config, 'DEFAULT_THEME', None))
        except Exception:
            logger.warning("Failed to apply theme; continuing without custom stylesheet")
        
        # Initialize database
        DatabaseManager.initialize()
        logger.info("Database initialized")

        # Show login dialog and require successful auth before showing main UI
        login = LoginDialog()
        if login.exec() != QDialog.Accepted:
            logger.info("Login cancelled, exiting")
            sys.exit(0)

        current_user = getattr(login, 'user', None)

        # Create and show main window with authenticated user
        window = MainWindow(current_user=current_user)
        window.show()
        
        logger.info("Application started successfully")
        
        # Run application
        sys.exit(app.exec())
    
    except Exception as e:
        logger.critical(f"Application failed to start: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
