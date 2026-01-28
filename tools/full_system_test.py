
import sys
import os
import shutil
import unittest
import logging
from datetime import datetime, date
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("SystemTest")

# Mock config to use test database
import egg_farm_system.config as config
TEST_DB = Path("test_egg_farm.db")
config.DB_PATH = TEST_DB
config.DATABASE_URL = f"sqlite:///{config.DB_PATH}"

# Import modules after config mock
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import Base
from egg_farm_system.modules.farms import FarmManager
from egg_farm_system.modules.sheds import ShedManager
from egg_farm_system.modules.flocks import FlockManager
from egg_farm_system.modules.feed_mill import RawMaterialManager, FeedFormulaManager, FeedProductionManager, FeedIssueManager
from egg_farm_system.database.models import FeedType
from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.modules.sales import SalesManager
from egg_farm_system.modules.purchases import PurchaseManager
from egg_farm_system.modules.expenses import ExpenseManager, PaymentManager
from egg_farm_system.modules.financial_reports import FinancialReportGenerator

class FullSystemTest(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        """Setup test database"""
        if TEST_DB.exists():
            os.remove(TEST_DB)
        
        DatabaseManager.initialize()
        # Tables are created by initialize()
        logger.info("Test database initialized")

    @classmethod
    def tearDownClass(cls):
        """Cleanup"""
        DatabaseManager.close()
        # if TEST_DB.exists():
        #     os.remove(TEST_DB)
        logger.info("Test completed")

    def test_01_farm_shed_creation(self):
        """Test creating farm and shed"""
        logger.info("Testing Farm & Shed Creation...")
        
        with FarmManager() as fm:
            farm = fm.create_farm("Test Farm", "Test Location")
            self.assertIsNotNone(farm.id)
            self.assertEqual(farm.name, "Test Farm")
            self.farm_id = farm.id
            
        with ShedManager() as sm:
            shed = sm.create_shed(self.farm_id, "Shed 1", 1000)
            self.assertIsNotNone(shed.id)
            self.shed_id = shed.id

    def test_02_flock_management(self):
        """Test flock creation and mortality"""
        logger.info("Testing Flock Management...")
        # Get IDs from previous steps (need to query or store in class var, but unittest runs independent instances usually? No, instance per test?)
        # Unittest creates new instance per test method. Need to query.
        
        with FarmManager() as fm:
            farm = fm.get_all_farms()[0]
            shed = farm.sheds[0]
            
        fm = FlockManager()
        flock = fm.create_flock(shed.id, "Flock A", datetime.utcnow(), 1000)
        self.assertIsNotNone(flock.id)
        
        fm.add_mortality(flock.id, datetime.utcnow(), 5)
        stats = fm.get_flock_stats(flock.id)
        self.assertEqual(stats['live_count'], 995)

    def test_03_feed_production(self):
        """Test feed workflow"""
        logger.info("Testing Feed Production...")
        
        # 1. Create Raw Materials
        with RawMaterialManager() as rmm:
            corn = rmm.create_material("Corn", 0, 0) # Cost is calculated from purchase now
            soya = rmm.create_material("Soya", 0, 0)
            
            # Purchase materials to establish stock and cost
            pm = PartyManager()
            supplier = pm.create_party("Feed Supplier", "123", "City")
            
            p_manager = PurchaseManager()
            # Buy 1000kg Corn @ 20 AFG
            p_manager.record_purchase(supplier.id, corn.id, 1000, 20, 0.25)
            # Buy 500kg Soya @ 50 AFG
            p_manager.record_purchase(supplier.id, soya.id, 500, 50, 0.6)
            
        # 2. Create Formula
        ffm = FeedFormulaManager()
        formula = ffm.create_formula("Standard Layer", FeedType.LAYER)
        
        # Add ingredients (60% Corn, 40% Soya)
        # Re-fetch material IDs
        with RawMaterialManager() as rmm:
            corn = next(m for m in rmm.get_all_materials() if m.name == "Corn")
            soya = next(m for m in rmm.get_all_materials() if m.name == "Soya")
            
        ffm.add_ingredient(formula.id, corn.id, 60)
        ffm.add_ingredient(formula.id, soya.id, 40)
        
        # 3. Produce Batch
        fpm = FeedProductionManager()
        batch = fpm.produce_batch(formula.id, 100, 78.0) # Produce 100kg
        
        self.assertEqual(batch.quantity_kg, 100)
        # Cost check: 
        # Corn: 20 * 60% = 12
        # Soya: 50 * 40% = 20
        # Total per kg = 32
        # Total batch = 3200
        self.assertAlmostEqual(batch.cost_afg, 3200, delta=1.0)
        
        # 4. Issue Feed
        fim = FeedIssueManager()
        # Need shed id
        with ShedManager() as sm:
            shed = sm.get_all_sheds()[0]
            
        # Need finished feed id
        session = DatabaseManager.get_session()
        from egg_farm_system.database.models import FinishedFeed
        feed = session.query(FinishedFeed).first()
        session.close()
        
        issue = fim.issue_feed(shed.id, feed.id, 10, datetime.utcnow())
        self.assertEqual(issue.cost_afg, 320) # 10kg * 32

    def test_04_sales_and_cash_flow(self):
        """Test sales and cash flow logic"""
        logger.info("Testing Sales & Cash Flow...")
        
        pm = PartyManager()
        customer = pm.create_party("Egg Customer", "555", "Market")
        
        # 1. Record Sale (Cash Method)
        sm = SalesManager()
        # Ensure sufficient egg inventory exists for the sale (test environment may be fresh)
        from egg_farm_system.modules.inventory import InventoryManager
        inv_mgr = InventoryManager()
        sess = DatabaseManager.get_session()
        try:
            # Add 200 eggs (large) to inventory to satisfy sale
            inv_mgr.add_eggs(sess, large=200)
            sess.commit()
        finally:
            sess.close()
        # Sell 100 eggs @ 10 AFG
        sale = sm.record_sale(customer.id, 100, 10, 0.1, payment_method="Cash")
        
        # Verify Party Balance (Should be 1000 Debit/Owed)
        # Because Sale is Accrual
        lm = SalesManager() # Or LedgerManager
        # We need LedgerManager to check balance
        # But Party model has helper
        session = DatabaseManager.get_session()
        p = session.query(customer.__class__).get(customer.id)
        balance = p.get_balance("AFG")
        self.assertEqual(balance, 1000)
        session.close()
        
        # 2. Check Cash Flow (Should be 0 Inflow)
        session = DatabaseManager.get_session()
        frg = FinancialReportGenerator(session)
        cf = frg.generate_cash_flow_statement(datetime.utcnow().date(), datetime.utcnow().date())
        # With the FIX applied, Sales are ignored. So Inflow should be 0.
        self.assertEqual(cf['inflows_from_sales'], 0)
        self.assertEqual(cf['total_inflows'], 0)
        
        # 3. Record Payment (Received)
        pay_m = PaymentManager()
        pay_m.record_payment(customer.id, 1000, 100, "Received", "Cash")
        
        # 4. Check Cash Flow Again (Should be 1000 Inflow)
        cf = frg.generate_cash_flow_statement(datetime.utcnow().date(), datetime.utcnow().date())
        self.assertEqual(cf['inflows_from_payments'], 1000)
        self.assertEqual(cf['total_inflows'], 1000)
        
        session.close()

if __name__ == '__main__':
    unittest.main()
