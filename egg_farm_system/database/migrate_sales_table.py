"""
Migration script to add new columns to sales table for advanced egg management
"""
from egg_farm_system.utils.i18n import tr

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def migrate_sales_table():
    """Add new columns to sales table if they don't exist"""
    conn = None
    try:
        # Import here to avoid circular imports
        from egg_farm_system.config import DB_PATH
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Check if columns exist and add them if they don't
        cursor.execute("PRAGMA table_info(sales)")
        columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = [
            ('cartons', 'REAL'),
            ('egg_grade', 'VARCHAR(20)'),
            ('tray_expense_afg', 'REAL'),
            ('carton_expense_afg', 'REAL'),
            ('total_expense_afg', 'REAL')
        ]
        
        for col_name, col_type in new_columns:
            if col_name not in columns:
                try:
                    cursor.execute(f"ALTER TABLE sales ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Added column '{col_name}' to sales table")
                except sqlite3.OperationalError as e:
                    logger.warning(f"Could not add column '{col_name}': {e}")
        
        conn.commit()
        logger.info("Sales table migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error migrating sales table: {e}")
        return False
    finally:
        if conn:
            conn.close()


if __name__ == "__main__":
    import sys
    from pathlib import Path
    # Add parent directory to path
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    
    logging.basicConfig(level=logging.INFO)
    migrate_sales_table()

