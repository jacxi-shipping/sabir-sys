"""
Migration script to add payment_method column to sales, purchases, and expenses tables
"""
from egg_farm_system.utils.i18n import tr

import logging
from egg_farm_system.database.db import DatabaseManager
from sqlalchemy import text

logger = logging.getLogger(__name__)

def migrate_payment_method():
    """Add payment_method column to sales, purchases, and expenses tables"""
    session = DatabaseManager.get_session()
    try:
        # Check and add payment_method to sales table
        try:
            session.execute(text("ALTER TABLE sales ADD COLUMN payment_method VARCHAR(20) DEFAULT 'Cash'"))
            logger.info("Added payment_method column to sales table")
        except Exception as e:
            msg = str(e).lower()
            if "duplicate column" in msg or "already exists" in msg:
                logger.info("payment_method column already exists in sales table")
            elif "no such table" in msg:
                logger.info("Sales table does not exist yet; skipping payment_method addition")
            else:
                raise
        
        # Check and add payment_method to purchases table
        try:
            session.execute(text("ALTER TABLE purchases ADD COLUMN payment_method VARCHAR(20) DEFAULT 'Cash'"))
            logger.info("Added payment_method column to purchases table")
        except Exception as e:
            msg = str(e).lower()
            if "duplicate column" in msg or "already exists" in msg:
                logger.info("payment_method column already exists in purchases table")
            elif "no such table" in msg:
                logger.info("Purchases table does not exist yet; skipping payment_method addition")
            else:
                raise
        
        # Check and add payment_method to expenses table
        try:
            session.execute(text("ALTER TABLE expenses ADD COLUMN payment_method VARCHAR(20) DEFAULT 'Cash'"))
            logger.info("Added payment_method column to expenses table")
        except Exception as e:
            msg = str(e).lower()
            if "duplicate column" in msg or "already exists" in msg:
                logger.info("payment_method column already exists in expenses table")
            elif "no such table" in msg:
                logger.info("Expenses table does not exist yet; skipping payment_method addition")
            else:
                raise
        
        session.commit()
        logger.info("Payment method migration completed successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Error during payment method migration: {e}")
        raise
    finally:
        session.close()

