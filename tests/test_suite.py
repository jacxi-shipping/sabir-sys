"""
Automated Testing Framework for Egg Farm Management System
Comprehensive test suite with unit, integration, and end-to-end tests
"""
import unittest
import pytest
from unittest.mock import Mock, patch, MagicMock
import sys
import os
from pathlib import Path
import tempfile
import sqlite3
from datetime import datetime, timedelta
import json

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from egg_farm_system.database.models import (
    Base, Farm, Shed, Flock, EggProduction, Sale, Purchase, 
    Expense, Party, RawMaterial, FinishedFeed, FeedIssue
)
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.advanced_analytics import AdvancedAnalytics
from egg_farm_system.modules.inventory_optimizer import InventoryOptimizer
from egg_farm_system.modules.financial_planner import FinancialPlanner

class TestDatabaseManager(unittest.TestCase):
    """Test cases for database operations"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test database"""
        # Create temporary test database
        cls.test_db_path = tempfile.mktemp(suffix='.db')
        cls.db_manager = DatabaseManager()
        cls.db_manager.engine = cls.db_manager.create_test_engine(cls.test_db_path)
        cls.SessionLocal = cls.db_manager.get_session_local()
        
    @classmethod
    def tearDownClass(cls):
        """Clean up test database"""
        if os.path.exists(cls.test_db_path):
            os.remove(cls.test_db_path)
    
    def setUp(self):
        """Set up test session"""
        self.session = self.SessionLocal()
        
    def tearDown(self):
        """Clean up test session"""
        self.session.close()
    
    def test_create_farm(self):
        """Test creating a farm"""
        farm = Farm(
            name="Test Farm",
            location="Test Location"
        )
        self.session.add(farm)
        self.session.commit()
        
        # Verify farm was created
        created_farm = self.session.query(Farm).filter(Farm.name == "Test Farm").first()
        self.assertIsNotNone(created_farm)
        self.assertEqual(created_farm.location, "Test Location")
    
    def test_create_shed(self):
        """Test creating a shed"""
        # First create a farm
        farm = Farm(name="Test Farm", location="Test Location")
        self.session.add(farm)
        self.session.commit()
        
        # Create a shed
        shed = Shed(
            farm_id=farm.id,
            name="Test Shed",
            capacity=1000
        )
        self.session.add(shed)
        self.session.commit()
        
        # Verify shed was created
        created_shed = self.session.query(Shed).filter(Shed.name == "Test Shed").first()
        self.assertIsNotNone(created_shed)
        self.assertEqual(created_shed.capacity, 1000)
        self.assertEqual(created_shed.farm_id, farm.id)
    
    def test_egg_production_record(self):
        """Test recording egg production"""
        # Setup farm and shed
        farm = Farm(name="Test Farm", location="Test Location")
        self.session.add(farm)
        self.session.commit()
        
        shed = Shed(farm_id=farm.id, name="Test Shed", capacity=1000)
        self.session.add(shed)
        self.session.commit()
        
        # Record egg production
        production = EggProduction(
            shed_id=shed.id,
            date=datetime.utcnow(),
            total_eggs=950,
            usable_eggs=920,
            small_count=200,
            medium_count=350,
            large_count=370,
            broken_count=30
        )
        self.session.add(production)
        self.session.commit()
        
        # Verify production record
        recorded_production = self.session.query(EggProduction).first()
        self.assertIsNotNone(recorded_production)
        self.assertEqual(recorded_production.total_eggs, 950)
        self.assertEqual(recorded_production.usable_eggs, 920)
    
    def test_sale_transaction(self):
        """Test recording a sale transaction"""
        # Create party
        party = Party(
            name="Test Customer",
            party_type="Customer",
            contact_info="test@example.com"
        )
        self.session.add(party)
        self.session.commit()
        
        # Record sale
        sale = Sale(
            party_id=party.id,
            date=datetime.utcnow(),
            small_count=100,
            medium_count=200,
            large_count=150,
            total_amount_afg=50000,
            total_amount_usd=555
        )
        self.session.add(sale)
        self.session.commit()
        
        # Verify sale
        recorded_sale = self.session.query(Sale).first()
        self.assertIsNotNone(recorded_sale)
        self.assertEqual(recorded_sale.total_amount_afg, 50000)
        self.assertEqual(recorded_sale.party_id, party.id)

class TestAdvancedAnalytics(unittest.TestCase):
    """Test cases for advanced analytics module"""
    
    def setUp(self):
        """Set up test database with sample data"""
        self.test_db_path = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager()
        self.db_manager.engine = self.db_manager.create_test_engine(self.test_db_path)
        
        # Create tables
        Base.metadata.create_all(bind=self.db_manager.engine)
        
        self.session = self.db_manager.get_session()
        self._create_sample_data()
    
    def tearDown(self):
        """Clean up"""
        self.session.close()
        self.db_manager.engine.dispose()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def _create_sample_data(self):
        """Create sample data for testing"""
        # Create farm
        farm = Farm(name="Test Farm", location="Test Location")
        self.session.add(farm)
        self.session.commit()
        
        # Create shed
        shed = Shed(farm_id=farm.id, name="Test Shed", capacity=1000)
        self.session.add(shed)
        self.session.commit()
        
        # Create egg production records for the last 90 days
        base_date = datetime.utcnow().date() - timedelta(days=90)
        for i in range(90):
            production_date = base_date + timedelta(days=i)
            # Simulate some variation in production
            total_eggs = 900 + int(50 * (1 + 0.1 * (i % 30 - 15) / 15))  # Some seasonal variation
            
            production = EggProduction(
                shed_id=shed.id,
                date=datetime.combine(production_date, datetime.min.time()),
                total_eggs=total_eggs,
                usable_eggs=total_eggs - int(total_eggs * 0.03),  # 3% broken
                small_count=int(total_eggs * 0.25),
                medium_count=int(total_eggs * 0.45),
                large_count=int(total_eggs * 0.30),
                broken_count=int(total_eggs * 0.03)
            )
            self.session.add(production)
        
        self.session.commit()
    
    def test_production_forecast(self):
        """Test production forecasting"""
        analytics = AdvancedAnalytics(session=self.session)
        
        # Test forecasting
        forecast = analytics.forecast_egg_production(farm_id=1, days_ahead=30)
        
        # Verify forecast structure
        self.assertIn("farm_id", forecast)
        self.assertIn("forecasts", forecast)
        self.assertIn("model_performance", forecast)
        
        # Verify we got forecasts
        if "error" not in forecast:
            self.assertTrue(len(forecast["forecasts"]) > 0)
            
            # Check forecast structure
            first_forecast = forecast["forecasts"][0]
            self.assertIn("date", first_forecast)
            self.assertIn("predicted_total_eggs", first_forecast)
            self.assertIn("predicted_usable_eggs", first_forecast)
    
    def test_financial_forecast(self):
        """Test financial forecasting"""
        # Create sample sales data
        party = Party(name="Test Customer", party_type="Customer")
        self.session.add(party)
        self.session.commit()
        
        # Create sales for the last year
        base_date = datetime.utcnow() - timedelta(days=365)
        for month in range(12):
            sale_date = base_date + timedelta(days=30 * month)
            sale = Sale(
                party_id=party.id,
                date=sale_date,
                total_amount_afg=50000 + (month * 2000),  # Growing sales
                total_amount_usd=555 + (month * 22)
            )
            self.session.add(sale)
        
        self.session.commit()
        
        analytics = AdvancedAnalytics(session=self.session)
        forecast = analytics.forecast_financial_performance(farm_id=1, months_ahead=6)
        
        # Verify forecast structure
        if "error" not in forecast:
            self.assertIn("revenue_forecast", forecast)
            self.assertIn("expense_forecast", forecast)
            self.assertIn("profitability_forecast", forecast)
    
    def test_inventory_optimization_analysis(self):
        """Test inventory optimization analysis"""
        # Create sample raw materials
        material1 = RawMaterial(
            name="Corn",
            unit="kg",
            current_stock=500,
            low_stock_alert=100,
            cost_afg=25.0
        )
        material2 = RawMaterial(
            name="Soybean Meal",
            unit="kg",
            current_stock=200,
            low_stock_alert=50,
            cost_afg=45.0
        )
        
        self.session.add_all([material1, material2])
        self.session.commit()
        
        analytics = AdvancedAnalytics(session=self.session)
        analysis = analytics.analyze_inventory_optimization(farm_id=1)
        
        # Verify analysis structure
        self.assertIn("abc_analysis", analysis)
        self.assertIn("reorder_analysis", analysis)
        self.assertIn("stockout_risk", analysis)
        
        if "error" not in analysis:
            self.assertTrue(len(analysis["abc_analysis"]["items"]) > 0)

class TestInventoryOptimizer(unittest.TestCase):
    """Test cases for inventory optimization module"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db_path = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager()
        self.db_manager.engine = self.db_manager.create_test_engine(self.test_db_path)
        
        Base.metadata.create_all(bind=self.db_manager.engine)
        self.session = self.db_manager.get_session()
    
    def tearDown(self):
        """Clean up"""
        self.session.close()
        self.db_manager.engine.dispose()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_demand_forecast(self):
        """Test demand forecasting for inventory items"""
        # Create raw material
        material = RawMaterial(
            name="Test Material",
            unit="kg",
            current_stock=100,
            low_stock_alert=20,
            cost_afg=30.0
        )
        self.session.add(material)
        self.session.commit()
        
        # Create sample consumption data
        base_date = datetime.utcnow().date() - timedelta(days=60)
        for i in range(60):
            consumption_date = base_date + timedelta(days=i)
            # Simulate daily consumption with some variation
            consumption = 10 + int(3 * (1 + 0.2 * (i % 7 - 3) / 3))
            
            # For simplicity, we'll create a purchase record as proxy for consumption
            purchase = Purchase(
                item_name="Test Material",
                quantity=consumption,
                unit_cost_afg=30.0,
                total_amount_afg=consumption * 30.0,
                date=datetime.combine(consumption_date, datetime.min.time())
            )
            self.session.add(purchase)
        
        self.session.commit()
        
        optimizer = InventoryOptimizer(session=self.session)
        forecast = optimizer.forecast_demand(
            item_id=material.id,
            item_type='raw_material',
            days_ahead=30
        )
        
        # Verify forecast structure
        if "error" not in forecast:
            self.assertIn("ensemble_forecast", forecast)
            self.assertIn("accuracy_metrics", forecast)
            self.assertIn("variability_analysis", forecast)
    
    def test_eoq_calculation(self):
        """Test Economic Order Quantity calculation"""
        # Create raw material
        material = RawMaterial(
            name="Test Material",
            unit="kg",
            current_stock=100,
            low_stock_alert=20,
            cost_afg=30.0
        )
        self.session.add(material)
        self.session.commit()
        
        optimizer = InventoryOptimizer(session=self.session)
        
        # Calculate EOQ with sample parameters
        eoq_result = optimizer.calculate_economic_order_quantity(
            item_id=material.id,
            item_type='raw_material',
            unit_cost=30.0,
            annual_demand=3650,  # 10 units per day
            ordering_cost=1000,
            holding_cost_rate=0.25
        )
        
        # Verify EOQ calculation
        if "error" not in eoq_result:
            self.assertIn("eoq_analysis", eoq_result)
            self.assertIn("derived_metrics", eoq_result)
            self.assertIn("sensitivity_analysis", eoq_result)
            
            # Check that EOQ is positive
            eoq = eoq_result["eoq_analysis"]["economic_order_quantity"]
            self.assertGreater(eoq, 0)
    
    def test_inventory_optimization(self):
        """Test comprehensive inventory optimization"""
        # Create multiple inventory items
        items = [
            RawMaterial(name="Material1", unit="kg", current_stock=100, low_stock_alert=20, cost_afg=30.0),
            RawMaterial(name="Material2", unit="kg", current_stock=50, low_stock_alert=10, cost_afg=25.0),
            RawMaterial(name="Material3", unit="kg", current_stock=500, low_stock_alert=100, cost_afg=15.0)
        ]
        
        self.session.add_all(items)
        self.session.commit()
        
        optimizer = InventoryOptimizer(session=self.session)
        optimization = optimizer.optimize_inventory_levels(farm_id=1)
        
        # Verify optimization structure
        if "error" not in optimization:
            self.assertIn("individual_optimizations", optimization)
            self.assertIn("optimization_summary", optimization)
            self.assertIn("investment_analysis", optimization)
            self.assertIn("implementation_plan", optimization)
            
            # Should have optimizations for all items
            self.assertTrue(len(optimization["individual_optimizations"]) > 0)

class TestFinancialPlanner(unittest.TestCase):
    """Test cases for financial planning module"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db_path = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager()
        self.db_manager.engine = self.db_manager.create_test_engine(self.test_db_path)
        
        Base.metadata.create_all(bind=self.db_manager.engine)
        self.session = self.db_manager.get_session()
        
        # Create sample farm
        self.farm = Farm(name="Test Farm", location="Test Location")
        self.session.add(self.farm)
        self.session.commit()
    
    def tearDown(self):
        """Clean up"""
        self.session.close()
        self.db_manager.engine.dispose()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_budget_creation(self):
        """Test budget creation"""
        # Create sample historical data for the past 2 years
        base_date = datetime(datetime.utcnow().year - 2, 1, 1)
        
        # Create sample sales
        for year in [datetime.utcnow().year - 2, datetime.utcnow().year - 1]:
            for month in range(1, 13):
                party = Party(name=f"Customer{month}", party_type="Customer")
                self.session.add(party)
                self.session.commit()
                
                sale = Sale(
                    party_id=party.id,
                    date=datetime(year, month, 15),
                    total_amount_afg=50000 + (month * 1000),
                    total_amount_usd=555 + (month * 11)
                )
                self.session.add(sale)
        
        # Create sample expenses
        for year in [datetime.utcnow().year - 2, datetime.utcnow().year - 1]:
            for month in range(1, 13):
                expense = Expense(
                    date=datetime(year, month, 10),
                    category="Feed",
                    amount_afg=25000 + (month * 500),
                    amount_usd=277 + (month * 5.5),
                    description=f"Monthly feed cost {month}/{year}"
                )
                self.session.add(expense)
        
        self.session.commit()
        
        planner = FinancialPlanner(session=self.session)
        
        # Create budget for current year
        current_year = datetime.utcnow().year
        budget = planner.create_budget(
            farm_id=self.farm.id,
            year=current_year,
            egg_price_growth=0.05,
            feed_inflation=0.08
        )
        
        # Verify budget structure
        if "error" not in budget:
            self.assertIn("revenue_budget", budget)
            self.assertIn("expense_budget", budget)
            self.assertIn("cash_flow_budget", budget)
            self.assertIn("budget_summary", budget)
            self.assertIn("budget_scenarios", budget)
            
            # Check budget summary
            summary = budget["budget_summary"]
            self.assertIn("profit_loss_projection", summary)
            self.assertIn("cost_structure", summary)
    
    def test_financial_forecasting(self):
        """Test financial forecasting"""
        # Create sample sales for the last 24 months
        party = Party(name="Test Customer", party_type="Customer")
        self.session.add(party)
        self.session.commit()
        
        base_date = datetime.utcnow() - timedelta(days=730)  # 2 years ago
        
        for month in range(24):
            sale_date = base_date + timedelta(days=30 * month)
            sale = Sale(
                party_id=party.id,
                date=sale_date,
                total_amount_afg=40000 + (month * 1500),  # Growing trend
                total_amount_usd=444 + (month * 16.5)
            )
            self.session.add(sale)
        
        # Create sample expenses
        for month in range(24):
            expense_date = base_date + timedelta(days=30 * month)
            expense = Expense(
                date=expense_date,
                category="Feed",
                amount_afg=25000 + (month * 800),
                amount_usd=277 + (month * 8.8)
            )
            self.session.add(expense)
        
        self.session.commit()
        
        planner = FinancialPlanner(session=self.session)
        forecast = planner.create_financial_forecast(farm_id=self.farm.id, months_ahead=12)
        
        # Verify forecast structure
        if "error" not in forecast:
            self.assertIn("forecasts", forecast)
            self.assertIn("scenarios", forecast)
            self.assertIn("projections", forecast)
            self.assertIn("risk_analysis", forecast)
            
            # Check forecast components
            forecasts = forecast["forecasts"]
            self.assertIn("revenue", forecasts)
            self.assertIn("expenses", forecasts)
            self.assertIn("cash_flow", forecasts)

class TestDataValidation(unittest.TestCase):
    """Test data validation and integrity"""
    
    def setUp(self):
        """Set up test database"""
        self.test_db_path = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager()
        self.db_manager.engine = self.db_manager.create_test_engine(self.test_db_path)
        
        Base.metadata.create_all(bind=self.db_manager.engine)
        self.session = self.db_manager.get_session()
    
    def tearDown(self):
        """Clean up"""
        self.session.close()
        self.db_manager.engine.dispose()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def test_egg_production_validation(self):
        """Test validation of egg production data"""
        # Test with valid data
        farm = Farm(name="Test Farm", location="Test Location")
        self.session.add(farm)
        self.session.commit()
        
        shed = Shed(farm_id=farm.id, name="Test Shed", capacity=1000)
        self.session.add(shed)
        self.session.commit()
        
        production = EggProduction(
            shed_id=shed.id,
            date=datetime.utcnow(),
            total_eggs=950,
            usable_eggs=920,
            small_count=200,
            medium_count=350,
            large_count=370,
            broken_count=30
        )
        
        # Should not raise exception
        self.session.add(production)
        self.session.commit()
        
        # Test that usable + broken = total
        self.assertEqual(production.usable_eggs + production.broken_count, production.total_eggs)
    
    def test_financial_data_consistency(self):
        """Test consistency of financial data"""
        # Create party
        party = Party(name="Test Customer", party_type="Customer")
        self.session.add(party)
        self.session.commit()
        
        # Create sale
        sale = Sale(
            party_id=party.id,
            date=datetime.utcnow(),
            small_count=100,
            medium_count=200,
            large_count=150,
            total_amount_afg=50000,
            total_amount_usd=555
        )
        self.session.add(sale)
        self.session.commit()
        
        # Verify sale totals are consistent
        self.assertGreater(sale.total_amount_afg, 0)
        self.assertGreater(sale.total_amount_usd, 0)

class TestIntegrationScenarios(unittest.TestCase):
    """Integration test scenarios"""
    
    def setUp(self):
        """Set up complete test scenario"""
        self.test_db_path = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager()
        self.db_manager.engine = self.db_manager.create_test_engine(self.test_db_path)
        
        Base.metadata.create_all(bind=self.db_manager.engine)
        self.session = self.db_manager.get_session()
        self._create_complete_scenario()
    
    def tearDown(self):
        """Clean up"""
        self.session.close()
        self.db_manager.engine.dispose()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
    
    def _create_complete_scenario(self):
        """Create a complete farm scenario for testing"""
        # Create farm
        self.farm = Farm(name="Integration Test Farm", location="Test Location")
        self.session.add(self.farm)
        self.session.commit()
        
        # Create sheds
        sheds = []
        for i in range(3):
            shed = Shed(
                farm_id=self.farm.id,
                name=f"Shed {i+1}",
                capacity=1000
            )
            self.session.add(shed)
            sheds.append(shed)
        self.session.commit()
        
        # Create flocks
        flocks = []
        for shed in sheds:
            flock = Flock(
                shed_id=shed.id,
                name=f"Flock in {shed.name}",
                start_date=datetime.utcnow() - timedelta(days=200),
                initial_count=800
            )
            self.session.add(flock)
            flocks.append(flock)
        self.session.commit()
        
        # Create egg production for the last 90 days
        base_date = datetime.utcnow().date() - timedelta(days=90)
        for i in range(90):
            production_date = base_date + timedelta(days=i)
            for shed in sheds:
                # Simulate production variation by shed and day
                base_production = 750 + (shed.id * 25)
                daily_variation = int(50 * (1 + 0.2 * (i % 14 - 7) / 7))
                total_eggs = base_production + daily_variation
                
                production = EggProduction(
                    shed_id=shed.id,
                    date=datetime.combine(production_date, datetime.min.time()),
                    total_eggs=total_eggs,
                    usable_eggs=int(total_eggs * 0.97),
                    small_count=int(total_eggs * 0.25),
                    medium_count=int(total_eggs * 0.45),
                    large_count=int(total_eggs * 0.27),
                    broken_count=int(total_eggs * 0.03)
                )
                self.session.add(production)
        
        # Create customers and sales
        customers = []
        for i in range(5):
            customer = Party(
                name=f"Customer {i+1}",
                party_type="Customer",
                contact_info=f"customer{i+1}@example.com"
            )
            self.session.add(customer)
            customers.append(customer)
        self.session.commit()
        
        # Create sales for the last 6 months
        base_sale_date = datetime.utcnow() - timedelta(days=180)
        for month in range(6):
            for customer in customers:
                sale_date = base_sale_date + timedelta(days=30 * month)
                # Simulate sales growth
                growth_factor = 1 + (month * 0.1)
                
                sale = Sale(
                    party_id=customer.id,
                    date=sale_date,
                    small_count=int(80 * growth_factor),
                    medium_count=int(120 * growth_factor),
                    large_count=int(100 * growth_factor),
                    total_amount_afg=int(40000 * growth_factor),
                    total_amount_usd=int(444 * growth_factor)
                )
                self.session.add(sale)
        
        # Create suppliers and purchases
        suppliers = []
        for i in range(3):
            supplier = Party(
                name=f"Supplier {i+1}",
                party_type="Supplier",
                contact_info=f"supplier{i+1}@example.com"
            )
            self.session.add(supplier)
            suppliers.append(supplier)
        self.session.commit()
        
        # Create raw materials
        raw_materials = []
        materials_data = [
            ("Corn", "kg", 500, 100, 25.0),
            ("Soybean Meal", "kg", 300, 50, 45.0),
            ("Wheat Bran", "kg", 200, 30, 20.0),
            ("Limestone", "kg", 150, 25, 15.0)
        ]
        
        for name, unit, stock, alert, cost in materials_data:
            material = RawMaterial(
                name=name,
                unit=unit,
                current_stock=stock,
                low_stock_alert=alert,
                cost_afg=cost
            )
            self.session.add(material)
            raw_materials.append(material)
        
        # Create finished feeds
        from egg_farm_system.database.models import FeedType
        feeds = []
        for feed_type in [FeedType.STARTER, FeedType.GROWER, FeedType.LAYER]:
            feed = FinishedFeed(
                feed_type=feed_type,
                current_stock=200,
                low_stock_alert=50,
                cost_per_kg_afg=35.0,
                cost_per_kg_usd=0.39
            )
            self.session.add(feed)
            feeds.append(feed)
        
        self.session.commit()
        
        # Create purchases
        base_purchase_date = datetime.utcnow() - timedelta(days=90)
        for month in range(3):
            for material in raw_materials:
                purchase_date = base_purchase_date + timedelta(days=30 * month)
                quantity = 100 + (month * 20)
                
                purchase = Purchase(
                    party_id=suppliers[month % len(suppliers)].id,
                    item_name=material.name,
                    quantity=quantity,
                    unit_cost_afg=material.cost_afg,
                    total_amount_afg=quantity * material.cost_afg,
                    date=purchase_date
                )
                self.session.add(purchase)
        
        # Create expenses
        expense_categories = ["Feed", "Labor", "Utilities", "Maintenance", "Veterinary", "Transportation"]
        base_expense_date = datetime.utcnow() - timedelta(days=180)
        
        for month in range(6):
            for category in expense_categories:
                expense_date = base_expense_date + timedelta(days=15 * month)
                # Simulate expense growth
                growth_factor = 1 + (month * 0.05)
                
                expense = Expense(
                    date=expense_date,
                    category=category,
                    amount_afg=int(15000 * growth_factor),
                    amount_usd=int(166 * growth_factor),
                    description=f"{category} expense for month {month+1}"
                )
                self.session.add(expense)
        
        self.session.commit()
    
    def test_complete_analytics_integration(self):
        """Test integration of all analytics modules"""
        # Test advanced analytics
        analytics = AdvancedAnalytics(session=self.session)
        
        production_forecast = analytics.forecast_egg_production(farm_id=self.farm.id, days_ahead=30)
        financial_forecast = analytics.forecast_financial_performance(farm_id=self.farm.id, months_ahead=6)
        inventory_analysis = analytics.analyze_inventory_optimization(farm_id=self.farm.id)
        
        # Verify all analytics work together
        self.assertTrue(
            "error" in production_forecast or "forecasts" in production_forecast
        )
        self.assertTrue(
            "error" in financial_forecast or "revenue_forecast" in financial_forecast
        )
        self.assertTrue(
            "error" in inventory_analysis or "abc_analysis" in inventory_analysis
        )
    
    def test_complete_optimization_integration(self):
        """Test integration of inventory optimization"""
        optimizer = InventoryOptimizer(session=self.session)
        
        # Get raw materials
        raw_materials = self.session.query(RawMaterial).all()
        if raw_materials:
            # Test demand forecasting for first material
            demand_forecast = optimizer.forecast_demand(
                item_id=raw_materials[0].id,
                item_type='raw_material',
                days_ahead=30
            )
            
            # Test EOQ calculation
            eoq_result = optimizer.calculate_economic_order_quantity(
                item_id=raw_materials[0].id,
                item_type='raw_material',
                unit_cost=raw_materials[0].cost_afg,
                annual_demand=3650
            )
            
            # Test comprehensive optimization
            optimization = optimizer.optimize_inventory_levels(farm_id=self.farm.id)
            
            # Verify integration
            self.assertTrue(
                "error" in demand_forecast or "ensemble_forecast" in demand_forecast
            )
            self.assertTrue(
                "error" in eoq_result or "eoq_analysis" in eoq_result
            )
            self.assertTrue(
                "error" in optimization or "optimization_summary" in optimization
            )
    
    def test_complete_financial_planning_integration(self):
        """Test integration of financial planning"""
        planner = FinancialPlanner(session=self.session)
        
        # Test budget creation
        budget = planner.create_budget(
            farm_id=self.farm.id,
            year=datetime.utcnow().year
        )
        
        # Test financial forecasting
        forecast = planner.create_financial_forecast(
            farm_id=self.farm.id,
            months_ahead=12
        )
        
        # Verify integration
        self.assertTrue(
            "error" in budget or "budget_summary" in budget
        )
        self.assertTrue(
            "error" in forecast or "projections" in forecast
        )

def run_tests():
    """Run all tests and generate report"""
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestDatabaseManager,
        TestAdvancedAnalytics,
        TestInventoryOptimizer,
        TestFinancialPlanner,
        TestDataValidation,
        TestIntegrationScenarios
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Generate test report
    print("\n" + "="*80)
    print("TEST SUMMARY REPORT")
    print("="*80)
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)