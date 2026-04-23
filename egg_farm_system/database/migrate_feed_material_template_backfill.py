"""
Backfill farm-scoped feed materials from a template set.

Ensures every farm has the same non-packaging material names so farm-scoped
sale/production dialogs don't miss expected feed materials.
"""

import logging

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Farm, RawMaterial

logger = logging.getLogger(__name__)

PACKAGING_NAMES = {"Carton", "Tray"}


def _pick_template_materials(session):
    """Build template materials as a union across farms (first row per name)."""
    rows = session.query(RawMaterial).filter(
        RawMaterial.name.notin_(PACKAGING_NAMES),
    ).order_by(RawMaterial.name.asc(), RawMaterial.farm_id.asc(), RawMaterial.id.asc()).all()

    template_by_name = {}
    for row in rows:
        if row.name not in template_by_name:
            template_by_name[row.name] = row

    return [template_by_name[name] for name in sorted(template_by_name.keys())]


def migrate_feed_material_template_backfill():
    session = DatabaseManager.get_session()
    try:
        template_materials = _pick_template_materials(session)
        if not template_materials:
            logger.info("Feed material template backfill skipped: no template materials found")
            session.commit()
            return

        farms = session.query(Farm).all()
        created_count = 0
        for farm in farms:
            for template in template_materials:
                exists = session.query(RawMaterial).filter(
                    RawMaterial.farm_id == farm.id,
                    RawMaterial.name == template.name,
                ).first()
                if exists:
                    continue

                row = RawMaterial(
                    farm_id=farm.id,
                    name=template.name,
                    unit=template.unit,
                    current_stock=0.0,
                    total_quantity_purchased=0.0,
                    total_cost_purchased_afg=0.0,
                    total_cost_purchased_usd=0.0,
                    low_stock_alert=template.low_stock_alert,
                )
                session.add(row)
                created_count += 1

        session.commit()
        logger.info("Feed material template backfill completed, created %s rows", created_count)
    except Exception as exc:
        session.rollback()
        logger.error("Feed material template backfill migration failed: %s", exc)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    migrate_feed_material_template_backfill()
