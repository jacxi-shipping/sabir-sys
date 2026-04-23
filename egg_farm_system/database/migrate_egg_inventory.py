"""
Migration to ensure `egg_inventory` rows and packaging materials exist.
"""
from egg_farm_system.database.db import DatabaseManager
from sqlalchemy import func

from egg_farm_system.database.models import EggInventory, EggGrade, RawMaterial, Farm, EggProduction, Shed, Sale
import logging

logger = logging.getLogger(__name__)


def migrate_egg_inventory():
    session = DatabaseManager.get_session()
    try:
        farms = session.query(Farm).all()

        for farm in farms:
            inventory_rows = []
            # Ensure egg inventory rows for all farm-scoped grades
            for g in (EggGrade.SMALL, EggGrade.MEDIUM, EggGrade.LARGE, EggGrade.BROKEN):
                row = session.query(EggInventory).filter(
                    EggInventory.farm_id == farm.id,
                    EggInventory.grade == g,
                ).first()
                if not row:
                    row = EggInventory(farm_id=farm.id, grade=g, current_stock=0)
                    session.add(row)
                inventory_rows.append(row)

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

            # Backfill inventory for farms that have production history but only empty rows.
            current_total = sum(int(row.current_stock or 0) for row in inventory_rows)
            if current_total == 0:
                produced = (
                    session.query(
                        func.coalesce(func.sum(EggProduction.small_count), 0),
                        func.coalesce(func.sum(EggProduction.medium_count), 0),
                        func.coalesce(func.sum(EggProduction.large_count), 0),
                        func.coalesce(func.sum(EggProduction.broken_count), 0),
                    )
                    .join(Shed, EggProduction.shed_id == Shed.id)
                    .filter(Shed.farm_id == farm.id)
                    .one()
                )
                produced_total = sum(int(value or 0) for value in produced)
                if produced_total > 0:
                    stock_by_grade = {
                        EggGrade.SMALL: int(produced[0] or 0),
                        EggGrade.MEDIUM: int(produced[1] or 0),
                        EggGrade.LARGE: int(produced[2] or 0),
                        EggGrade.BROKEN: int(produced[3] or 0),
                    }
                    sold_usable = int(
                        session.query(func.coalesce(func.sum(Sale.quantity), 0))
                        .filter(Sale.farm_id == farm.id)
                        .scalar()
                        or 0
                    )
                    remaining = sold_usable
                    for grade in (EggGrade.LARGE, EggGrade.MEDIUM, EggGrade.SMALL):
                        if remaining <= 0:
                            break
                        take = min(stock_by_grade[grade], remaining)
                        stock_by_grade[grade] -= take
                        remaining -= take

                    for row in inventory_rows:
                        row.current_stock = max(stock_by_grade.get(row.grade, 0), 0)

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
