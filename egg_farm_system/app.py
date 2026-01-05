"""
Main application entry point
"""
import sys
import logging
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from PySide6.QtWidgets import QApplication, QDialog
from egg_farm_system.database.db import DatabaseManager
from ui.main_window import MainWindow
from ui.forms.login_dialog import LoginDialog
from egg_farm_system.config import APP_NAME, APP_VERSION, LOGS_DIR, LOG_LEVEL, LOG_FORMAT

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
        # Load global stylesheet if present
        try:
            qss_path = Path(__file__).parent / "styles.qss"
            if qss_path.exists():
                with open(qss_path, 'r', encoding='utf-8') as f:
                    app.setStyleSheet(f.read())
        except Exception:
            pass
        
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
