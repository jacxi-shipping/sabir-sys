"""
Migration script to add farm_id to sales and purchases tables
"""
import sqlite3
import os
import logging

logger = logging.getLogger(__name__)

def migrate_add_farm_id():
    """Add farm_id column to sales and purchases tables"""
    # Database path
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'egg_farm.db')
    
    if not os.path.exists(db_path):
        logger.info("Database not found, migration not needed")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if farm_id already exists in sales table
        cursor.execute("PRAGMA table_info(sales)")
        sales_columns = [col[1] for col in cursor.fetchall()]
        
        if 'farm_id' not in sales_columns:
            logger.info("Adding farm_id to sales table")
            cursor.execute("ALTER TABLE sales ADD COLUMN farm_id INTEGER")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sale_farm_id ON sales(farm_id)")
            logger.info("farm_id added to sales table")
        else:
            logger.info("farm_id already exists in sales table")
        
        # Check if farm_id already exists in purchases table
        cursor.execute("PRAGMA table_info(purchases)")
        purchases_columns = [col[1] for col in cursor.fetchall()]
        
        if 'farm_id' not in purchases_columns:
            logger.info("Adding farm_id to purchases table")
            cursor.execute("ALTER TABLE purchases ADD COLUMN farm_id INTEGER")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_purchase_farm_id ON purchases(farm_id)")
            logger.info("farm_id added to purchases table")
        else:
            logger.info("farm_id already exists in purchases table")
        
        conn.commit()
        logger.info("Migration completed successfully")
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_add_farm_id()
