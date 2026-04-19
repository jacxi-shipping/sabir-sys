"""
Migration to ensure `egg_inventory` rows and packaging materials exist.
"""
from datetime import datetime
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import EggInventory, EggGrade, RawMaterial, Farm
import logging

logger = logging.getLogger(__name__)


def migrate_egg_inventory():
    session = DatabaseManager.get_session()
    try:
        farms = session.query(Farm).all()

        for farm in farms:
            # Ensure egg inventory rows for all farm-scoped grades
            for g in (EggGrade.SMALL, EggGrade.MEDIUM, EggGrade.LARGE, EggGrade.BROKEN):
                row = session.query(EggInventory).filter(
                    EggInventory.farm_id == farm.id,
                    EggInventory.grade == g,
                ).first()
                if not row:
                    row = EggInventory(farm_id=farm.id, grade=g, current_stock=0)
                    session.add(row)

            # Ensure farm-scoped packaging materials exist
            carton = session.query(RawMaterial).filter(
                RawMaterial.farm_id == farm.id,
                RawMaterial.name == 'Carton',
            ).first()
            if not carton:
                carton = RawMaterial(farm_id=farm.id, name='Carton', unit='pcs', current_stock=0)
                session.add(carton)

            tray = session.query(RawMaterial).filter(
                RawMaterial.farm_id == farm.id,
                RawMaterial.name == 'Tray',
            ).first()
            if not tray:
                tray = RawMaterial(farm_id=farm.id, name='Tray', unit='pcs', current_stock=0)
                session.add(tray)

        session.commit()
        logger.info('Egg inventory migration applied')
    except Exception as e:
        session.rollback()
        logger.error(f'Error applying egg inventory migration: {e}')
        raise
    finally:
        session.close()


if __name__ == '__main__':
    migrate_egg_inventory()
