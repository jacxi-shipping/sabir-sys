"""
Migration to add `cartons_used` and `trays_used` columns to `egg_productions` table if missing.
"""
from egg_farm_system.database.db import DatabaseManager
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)


def migrate_egg_production_packaging():
    engine = DatabaseManager._engine
    if engine is None:
        DatabaseManager.initialize()
        engine = DatabaseManager._engine

    conn = engine.connect()
    try:
        # Check existing columns via PRAGMA
        res = conn.execute(text("PRAGMA table_info('egg_productions')")).fetchall()
        cols = {r[1] for r in res}
        to_add = []
        if 'cartons_used' not in cols:
            to_add.append(("cartons_used", "INTEGER", "0"))
        if 'trays_used' not in cols:
            to_add.append(("trays_used", "INTEGER", "0"))

        for name, typ, default in to_add:
            sql = text(f"ALTER TABLE egg_productions ADD COLUMN {name} {typ} DEFAULT {default}")
            conn.execute(sql)
            logger.info(f"Added column {name} to egg_productions")
    except Exception as e:
        logger.error(f"Error migrating egg_productions packaging columns: {e}")
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    migrate_egg_production_packaging()
