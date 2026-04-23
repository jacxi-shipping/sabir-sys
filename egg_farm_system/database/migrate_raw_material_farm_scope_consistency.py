"""
Migration to align raw materials with the farms that actually purchased them.

This repairs legacy data where farm-scoped purchases still point at a raw material
row assigned to a different farm, which makes farm-filtered dialogs show only
packaging rows.
"""

import logging

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Purchase, RawMaterial

logger = logging.getLogger(__name__)


def migrate_raw_material_farm_scope_consistency():
    session = DatabaseManager.get_session()
    try:
        materials = session.query(RawMaterial).all()

        for material in materials:
            purchase_farm_ids = {
                farm_id
                for (farm_id,) in session.query(Purchase.farm_id)
                .filter(Purchase.material_id == material.id, Purchase.farm_id.is_not(None))
                .distinct()
                .all()
                if farm_id is not None
            }

            if len(purchase_farm_ids) != 1:
                continue

            target_farm_id = next(iter(purchase_farm_ids))
            if material.farm_id == target_farm_id:
                continue

            conflict = session.query(RawMaterial).filter(
                RawMaterial.farm_id == target_farm_id,
                RawMaterial.name == material.name,
                RawMaterial.id != material.id,
            ).first()
            if conflict:
                logger.warning(
                    "Skipping raw material farm alignment for %s because farm %s already has a row",
                    material.name,
                    target_farm_id,
                )
                continue

            logger.info(
                "Reassigning raw material %s from farm %s to farm %s based on purchase history",
                material.name,
                material.farm_id,
                target_farm_id,
            )
            material.farm_id = target_farm_id
            session.add(material)

        session.commit()
        logger.info("Raw material farm scope consistency migration completed")
    except Exception as exc:
        session.rollback()
        logger.error("Raw material farm scope consistency migration failed: %s", exc)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    migrate_raw_material_farm_scope_consistency()