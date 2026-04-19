"""
Migration to add farm scoping to inventory/accounting tables.

Tables covered:
- raw_materials: add farm_id and farm-scoped uniqueness for name
- finished_feeds: add farm_id
- egg_inventory: add farm_id and farm-scoped uniqueness for grade
- ledgers: add farm_id
"""

import logging
import sqlite3

from egg_farm_system.config import DATABASE_URL

logger = logging.getLogger(__name__)


def _db_path_from_url(db_url: str) -> str:
    if db_url.startswith("sqlite:///"):
        return db_url.replace("sqlite:///", "", 1)
    return db_url


def _column_exists(cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table_name})")
    return column_name in {row[1] for row in cursor.fetchall()}


def _get_or_create_default_farm_id(cursor) -> int:
    cursor.execute("SELECT id FROM farms ORDER BY id LIMIT 1")
    row = cursor.fetchone()
    if row:
        return int(row[0])

    cursor.execute("INSERT INTO farms (name, location) VALUES (?, ?)", ("Default Farm", "Migrated"))
    return int(cursor.lastrowid)


def _rebuild_raw_materials_for_farm_scoping(cursor):
    """Rebuild raw_materials to remove global UNIQUE(name) and enforce UNIQUE(farm_id, name)."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_materials_new (
            id INTEGER PRIMARY KEY,
            farm_id INTEGER REFERENCES farms(id),
            name VARCHAR(100) NOT NULL,
            unit VARCHAR(50) DEFAULT 'kg',
            current_stock FLOAT DEFAULT 0.0,
            total_quantity_purchased FLOAT NOT NULL DEFAULT 0.0,
            total_cost_purchased_afg FLOAT NOT NULL DEFAULT 0.0,
            total_cost_purchased_usd FLOAT NOT NULL DEFAULT 0.0,
            supplier_id INTEGER REFERENCES parties(id),
            low_stock_alert FLOAT DEFAULT 50,
            created_at DATETIME,
            updated_at DATETIME,
            CONSTRAINT uq_raw_material_farm_name UNIQUE (farm_id, name)
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO raw_materials_new (
            id, farm_id, name, unit, current_stock,
            total_quantity_purchased, total_cost_purchased_afg, total_cost_purchased_usd,
            supplier_id, low_stock_alert, created_at, updated_at
        )
        SELECT
            id, farm_id, name, unit, current_stock,
            total_quantity_purchased, total_cost_purchased_afg, total_cost_purchased_usd,
            supplier_id, low_stock_alert, created_at, updated_at
        FROM raw_materials
        """
    )

    cursor.execute("DROP TABLE raw_materials")
    cursor.execute("ALTER TABLE raw_materials_new RENAME TO raw_materials")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_material_farm_id ON raw_materials(farm_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_material_supplier_id ON raw_materials(supplier_id)")


def _rebuild_egg_inventory_for_farm_scoping(cursor):
    """Rebuild egg_inventory to remove global UNIQUE(grade) and enforce UNIQUE(farm_id, grade)."""
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS egg_inventory_new (
            id INTEGER PRIMARY KEY,
            farm_id INTEGER REFERENCES farms(id),
            grade VARCHAR(20) NOT NULL,
            current_stock INTEGER NOT NULL DEFAULT 0,
            created_at DATETIME,
            updated_at DATETIME,
            CONSTRAINT uq_egg_inventory_farm_grade UNIQUE (farm_id, grade)
        )
        """
    )

    cursor.execute(
        """
        INSERT INTO egg_inventory_new (
            id, farm_id, grade, current_stock, created_at, updated_at
        )
        SELECT
            id, farm_id, grade, current_stock, created_at, updated_at
        FROM egg_inventory
        """
    )

    cursor.execute("DROP TABLE egg_inventory")
    cursor.execute("ALTER TABLE egg_inventory_new RENAME TO egg_inventory")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_egg_inventory_farm_id ON egg_inventory(farm_id)")


def migrate_farm_scope_inventory_accounting():
    db_path = _db_path_from_url(DATABASE_URL)
    conn = sqlite3.connect(db_path)

    try:
        cursor = conn.cursor()

        default_farm_id = _get_or_create_default_farm_id(cursor)

        # Add farm_id columns when missing.
        if not _column_exists(cursor, "raw_materials", "farm_id"):
            cursor.execute("ALTER TABLE raw_materials ADD COLUMN farm_id INTEGER")

        if not _column_exists(cursor, "finished_feeds", "farm_id"):
            cursor.execute("ALTER TABLE finished_feeds ADD COLUMN farm_id INTEGER")

        if not _column_exists(cursor, "egg_inventory", "farm_id"):
            cursor.execute("ALTER TABLE egg_inventory ADD COLUMN farm_id INTEGER")

        if not _column_exists(cursor, "ledgers", "farm_id"):
            cursor.execute("ALTER TABLE ledgers ADD COLUMN farm_id INTEGER")

        # Backfill farm_id on existing rows.
        cursor.execute("UPDATE raw_materials SET farm_id = ? WHERE farm_id IS NULL", (default_farm_id,))
        cursor.execute("UPDATE finished_feeds SET farm_id = ? WHERE farm_id IS NULL", (default_farm_id,))
        cursor.execute("UPDATE egg_inventory SET farm_id = ? WHERE farm_id IS NULL", (default_farm_id,))

        # Ledger backfill from reference transaction farm first.
        cursor.execute(
            """
            UPDATE ledgers
            SET farm_id = (
                CASE
                    WHEN reference_type = 'Sale' THEN (
                        SELECT sales.farm_id FROM sales WHERE sales.id = ledgers.reference_id
                    )
                    WHEN reference_type = 'Purchase' THEN (
                        SELECT purchases.farm_id FROM purchases WHERE purchases.id = ledgers.reference_id
                    )
                    WHEN reference_type = 'Expense' THEN (
                        SELECT expenses.farm_id FROM expenses WHERE expenses.id = ledgers.reference_id
                    )
                    ELSE farm_id
                END
            )
            WHERE farm_id IS NULL
            """
        )
        cursor.execute("UPDATE ledgers SET farm_id = ? WHERE farm_id IS NULL", (default_farm_id,))

        # Rebuild constrained tables for farm-scoped uniqueness.
        cursor.execute("PRAGMA foreign_keys=OFF")
        _rebuild_raw_materials_for_farm_scoping(cursor)
        _rebuild_egg_inventory_for_farm_scoping(cursor)
        cursor.execute("PRAGMA foreign_keys=ON")

        # Helpful indexes for filtered queries.
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_finished_feed_farm_id ON finished_feeds(farm_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_ledger_farm_id ON ledgers(farm_id)")

        conn.commit()
        logger.info("Farm scoping migration for inventory/accounting completed successfully")

    except Exception as exc:
        conn.rollback()
        logger.error(f"Farm scoping migration failed: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    migrate_farm_scope_inventory_accounting()
