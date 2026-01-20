"""
Quick verification script for egg inventory and packaging materials.
Run: python tools/verify_inventory_setup.py
"""
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import EggInventory, RawMaterial

if __name__ == '__main__':
    DatabaseManager.initialize()
    session = DatabaseManager.get_session()
    try:
        eggs = session.query(EggInventory).all()
        print('EggInventory rows:')
        for e in eggs:
            print(f' - {e.grade.name}: {e.current_stock}')
        carton = session.query(RawMaterial).filter(RawMaterial.name=='Carton').first()
        tray = session.query(RawMaterial).filter(RawMaterial.name=='Tray').first()
        print('Carton current_stock:', carton.current_stock if carton else 'MISSING')
        print('Tray current_stock:', tray.current_stock if tray else 'MISSING')
    finally:
        session.close()
        DatabaseManager.close()
