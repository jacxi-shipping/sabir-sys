"""
Migration script to add average cost calculation columns to raw_materials table
"""
from egg_farm_system.utils.i18n import tr

import sqlite3
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def migrate_raw_materials_avg_cost():
    """Add average cost calculation columns to raw_materials table if they don't exist"""
    conn = None
    try:
        # Import here to avoid circular imports
        from egg_farm_system.config import DB_PATH
        
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # Check if columns exist and add them if they don't
        cursor.execute("PRAGMA table_info(raw_materials)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Whitelist of allowed columns to prevent SQL injection
        allowed_columns = {
            'total_quantity_purchased': 'REAL NOT NULL DEFAULT 0.0',
            'total_cost_purchased_afg': 'REAL NOT NULL DEFAULT 0.0',
            'total_cost_purchased_usd': 'REAL NOT NULL DEFAULT 0.0'
        }
        
        new_columns = [
            ('total_quantity_purchased', 'REAL NOT NULL DEFAULT 0.0'),
            ('total_cost_purchased_afg', 'REAL NOT NULL DEFAULT 0.0'),
            ('total_cost_purchased_usd', 'REAL NOT NULL DEFAULT 0.0')
        ]
        
        for col_name, col_type in new_columns:
            # Validate against whitelist before executing SQL
            if col_name not in allowed_columns:
                logger.error(f"Column '{col_name}' not in whitelist, skipping for security")
                continue
            if allowed_columns[col_name] != col_type:
                logger.error(f"Column type mismatch for '{col_name}', skipping for security")
                continue
                
            if col_name not in columns:
                try:
                    # Column name validated against whitelist above
                    cursor.execute(f"ALTER TABLE raw_materials ADD COLUMN {col_name} {col_type}")
                    logger.info(f"Added column '{col_name}' to raw_materials table")
                except sqlite3.OperationalError as e:
                    logger.warning(f"Could not add column '{col_name}': {e}")
        
        # Update existing records: calculate initial values from purchases if any exist
        try:
            cursor.execute("""
                UPDATE raw_materials
                SET 
                    total_quantity_purchased = (
                        SELECT COALESCE(SUM(quantity), 0.0)
                        FROM purchases
                        WHERE purchases.material_id = raw_materials.id
                    ),
                    total_cost_purchased_afg = (
                        SELECT COALESCE(SUM(total_afg), 0.0)
                        FROM purchases
                        WHERE purchases.material_id = raw_materials.id
                    ),
                    total_cost_purchased_usd = (
                        SELECT COALESCE(SUM(total_usd), 0.0)
                        FROM purchases
                        WHERE purchases.material_id = raw_materials.id
                    )
                WHERE EXISTS (
                    SELECT 1 FROM purchases WHERE purchases.material_id = raw_materials.id
                )
            """)
            updated_count = cursor.rowcount
            if updated_count > 0:
                logger.info(f"Updated {updated_count} raw materials with purchase history")
        except Exception as e:
            logger.warning(f"Could not update existing records with purchase data: {e}")
        
        conn.commit()
        logger.info("Raw materials average cost migration completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error migrating raw_materials table: {e}")
        if conn:
            conn.rollback()
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
    migrate_raw_materials_avg_cost()

