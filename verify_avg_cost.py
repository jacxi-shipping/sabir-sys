import sys
import os
from pathlib import Path

# Add current dir to sys.path
sys.path.append(os.getcwd())

# Mock DATABASE_URL before importing other modules
import egg_farm_system.config
TEST_DB_PATH = Path("verify_test.db").absolute()
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()
    
egg_farm_system.config.DATABASE_URL = f"sqlite:///{TEST_DB_PATH}"

from unittest.mock import MagicMock
sys.modules['egg_farm_system.database.migrate_sales_table'] = MagicMock()
sys.modules['egg_farm_system.database.migrate_payment_method'] = MagicMock()

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Base, Party, RawMaterial, Purchase
from egg_farm_system.modules.purchases import PurchaseManager
from sqlalchemy import text

def verify_wac():
    print("Registered tables:", Base.metadata.tables.keys())
    print("Initializing File Database:", TEST_DB_PATH)
    print("Database URL:", egg_farm_system.config.DATABASE_URL)
    DatabaseManager.initialize()
    Base.metadata.create_all(bind=DatabaseManager._engine)
    
    # Debug: Check if tables exist
    with DatabaseManager._engine.connect() as conn:
        result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        print("Existing tables in DB:", [row[0] for row in result])
    
    session = DatabaseManager.get_session()
    
    try:
        # 1. Create Supplier
        supplier = Party(name="Test Supplier", phone="123", address="Test Addr")
        session.add(supplier)
        session.commit()
        supplier_id = supplier.id
        print(f"Created Supplier ID: {supplier_id}")
        
        # 2. Create Raw Material (Initial State)
        # 10 units @ 100 AFG each = 1000 Total Value
        material = RawMaterial(
            name="Corn",
            current_stock=10.0,
            cost_afg=100.0,
            cost_usd=1.28, # Dummy
            supplier_id=supplier_id
        )
        session.add(material)
        session.commit()
        material_id = material.id
        print(f"Created Raw Material: Stock={material.current_stock}, Cost AFG={material.cost_afg}")
        
        # 3. Record Purchase
        # Buy 10 units @ 200 AFG each = 2000 Total Value
        # Expected New State:
        # Total Units = 10 + 10 = 20
        # Total Value = 1000 + 2000 = 3000
        # New Average Cost = 3000 / 20 = 150
        
        print("Recording Purchase: 10 units @ 200 AFG...")
        with PurchaseManager() as pm:
             pm.record_purchase(
                 party_id=supplier_id,
                 material_id=material_id,
                 quantity=10.0,
                 rate_afg=200.0,
                 rate_usd=2.56,
                 exchange_rate_used=78.0
             )
        
        # 4. Verify
        session.expire(material) # Refresh from DB
        session.refresh(material)
        
        print(f"New State: Stock={material.current_stock}, Cost AFG={material.cost_afg}")
        
        expected_cost = 150.0
        if abs(material.cost_afg - expected_cost) < 0.01:
            print("SUCCESS: Cost updated correctly using Weighted Average Cost.")
        else:
            print(f"FAILURE: Expected cost {expected_cost}, got {material.cost_afg}")
            sys.exit(1)
            
        if material.current_stock != 20.0:
            print(f"FAILURE: Expected stock 20.0, got {material.current_stock}")
            sys.exit(1)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()
        DatabaseManager.close()

if __name__ == "__main__":
    verify_wac()