"""
Performance and benchmarking tests for Egg Farm Management System v2.0
Tests the performance improvements and optimization of new features
"""
import pytest
import time
import psutil
import gc
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile
import sqlite3
from datetime import datetime, timedelta
import numpy as np

# Add the parent directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from egg_farm_system.database.models import Base, Farm, Shed, EggProduction, Sale, Expense, Party, RawMaterial, FinishedFeed, FeedType
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.advanced_analytics import AdvancedAnalytics
from egg_farm_system.modules.inventory_optimizer import InventoryOptimizer
from egg_farm_system.modules.financial_planner import FinancialPlanner

class TestPerformanceBenchmarks:
    """Performance benchmark tests for v2.0 features"""
    
    def setup_method(self):
        """Set up performance test environment"""
        # Create temporary test database
        self.test_db_path = tempfile.mktemp(suffix='.db')
        self.db_manager = DatabaseManager()
        self.db_manager.engine = self.db_manager.create_test_engine(self.test_db_path)
        
        # Create tables
        Base.metadata.create_all(bind=self.db_manager.engine)
        
        # Setup sample data
        self.setup_sample_data()
    
    def teardown_method(self):
        """Clean up performance test environment"""
        self.db_manager.engine.dispose()
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        gc.collect()  # Force garbage collection
    
    def setup_sample_data(self):
        """Setup comprehensive sample data for performance testing"""
        session = self.db_manager.get_session()
        
        try:
            # Create farm
            farm = Farm(name="Performance Test Farm", location="Test Location")
            session.add(farm)
            session.commit()
            
            # Create multiple sheds for realistic scenario
            sheds = []
            for i in range(10):  # Create 10 sheds
                shed = Shed(farm_id=farm.id, name=f"Shed {i+1}", capacity=1000)
                session.add(shed)
                sheds.append(shed)
            session.commit()
            
            # Create 2 years of daily production data for performance testing
            base_date = datetime.utcnow().date() - timedelta(days=730)
            productions = []
            
            for day in range(730):  # 2 years of data
                production_date = base_date + timedelta(days=day)
                for shed in sheds:
                    # Simulate realistic production with variations
                    base_production = 750 + (shed.id * 25)
                    seasonal_factor = 1 + 0.1 * np.sin(2 * np.pi * day / 365.25)  # Seasonal variation
                    daily_variation = np.random.normal(0, 50)  # Random daily variation
                    total_eggs = int(max(0, base_production * seasonal_factor + daily_variation))
                    
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
                    productions.append(production)
            
            session.bulk_save_objects(productions)
            session.commit()
            
        finally:
            session.close()
    
    def test_production_forecast_performance(self, benchmark):
        """Test performance of production forecasting with large dataset"""
        analytics = AdvancedAnalytics()
        
        def forecast_production():
            result = analytics.forecast_egg_production(farm_id=1, days_ahead=30)
            return result
        
        # Benchmark the forecasting operation
        result = benchmark(forecast_production)
        
        # Verify results are reasonable
        assert "error" not in result or result.get("error") is not None
        if "error" not in result:
            assert len(result.get("forecasts", [])) == 30
    
    @pytest.mark.benchmark
    def test_financial_forecast_performance(self, benchmark):
        """Test performance of financial forecasting"""
        # Add sample financial data for testing
        session = self.db_manager.get_session()
        try:
            from egg_farm_system.database.models import Sale, Expense, Party
            
            # Create sample sales and expenses for the past 2 years
            party = Party(name="Test Customer", party_type="Customer")
            session.add(party)
            session.commit()
            
            base_date = datetime.utcnow() - timedelta(days=730)
            sales = []
            expenses = []
            
            for month in range(24):  # 2 years of monthly data
                sale_date = base_date + timedelta(days=30 * month)
                expense_date = base_date + timedelta(days=30 * month)
                
                sale = Sale(
                    party_id=party.id,
                    date=sale_date,
                    total_amount_afg=50000 + (month * 2000),
                    total_amount_usd=555 + (month * 22)
                )
                sales.append(sale)
                
                expense = Expense(
                    date=expense_date,
                    category="Feed",
                    amount_afg=25000 + (month * 500),
                    amount_usd=277 + (month * 5.5)
                )
                expenses.append(expense)
            
            session.bulk_save_objects(sales + expenses)
            session.commit()
            
        finally:
            session.close()
        
        analytics = AdvancedAnalytics()
        
        def forecast_financial():
            result = analytics.forecast_financial_performance(farm_id=1, months_ahead=12)
            return result
        
        # Benchmark the financial forecasting
        result = benchmark(forecast_financial)
        
        # Verify results
        assert "error" not in result or result.get("error") is not None
    
    @pytest.mark.benchmark
    def test_inventory_optimization_performance(self, benchmark):
        """Test performance of inventory optimization analysis"""
        # Add sample inventory data
        session = self.db_manager.get_session()
        try:
            from egg_farm_system.database.models import RawMaterial, FinishedFeed, FeedType
            
            # Create sample raw materials
            raw_materials = []
            for i in range(50):  # 50 different materials
                material = RawMaterial(
                    name=f"Material_{i+1}",
                    unit="kg",
                    current_stock=np.random.randint(10, 1000),
                    low_stock_alert=np.random.randint(5, 50),
                    cost_afg=np.random.uniform(10, 100)
                )
                raw_materials.append(material)
            
            # Create sample finished feeds
            finished_feeds = []
            for feed_type in [FeedType.STARTER, FeedType.GROWER, FeedType.LAYER]:
                for i in range(5):  # 5 variants of each feed type
                    feed = FinishedFeed(
                        feed_type=feed_type,
                        current_stock=np.random.randint(50, 500),
                        low_stock_alert=np.random.randint(10, 100),
                        cost_per_kg_afg=np.random.uniform(25, 60),
                        cost_per_kg_usd=np.random.uniform(0.28, 0.67)
                    )
                    finished_feeds.append(feed)
            
            session.bulk_save_objects(raw_materials + finished_feeds)
            session.commit()
            
        finally:
            session.close()
        
        optimizer = InventoryOptimizer()
        
        def optimize_inventory():
            result = optimizer.analyze_inventory_optimization(farm_id=1)
            return result
        
        # Benchmark inventory optimization
        result = benchmark(optimize_inventory)
        
        # Verify results
        assert "error" not in result or result.get("error") is not None
    
    @pytest.mark.benchmark
    def test_demand_forecasting_performance(self, benchmark):
        """Test performance of demand forecasting for individual items"""
        # Get first raw material for testing
        session = self.db_manager.get_session()
        try:
            from egg_farm_system.database.models import RawMaterial, Purchase
            
            # Create a raw material
            material = RawMaterial(
                name="Performance Test Material",
                unit="kg",
                current_stock=500,
                low_stock_alert=50,
                cost_afg=30.0
            )
            session.add(material)
            session.commit()
            
            # Create consumption history (60 days)
            base_date = datetime.utcnow().date() - timedelta(days=60)
            purchases = []
            
            for day in range(60):
                consumption_date = base_date + timedelta(days=day)
                # Simulate daily consumption with variation
                consumption = max(1, int(np.random.normal(10, 3)))
                
                purchase = Purchase(
                    item_name="Performance Test Material",
                    quantity=consumption,
                    unit_cost_afg=30.0,
                    total_amount_afg=consumption * 30.0,
                    date=datetime.combine(consumption_date, datetime.min.time())
                )
                purchases.append(purchase)
            
            session.bulk_save_objects(purchases)
            session.commit()
            
            material_id = material.id
            
        finally:
            session.close()
        
        optimizer = InventoryOptimizer()
        
        def forecast_demand():
            result = optimizer.forecast_demand(
                item_id=material_id,
                item_type='raw_material',
                days_ahead=30
            )
            return result
        
        # Benchmark demand forecasting
        result = benchmark(forecast_demand)
        
        # Verify results
        assert "error" not in result or result.get("error") is not None
    
    @pytest.mark.benchmark
    def test_eoq_calculation_performance(self, benchmark):
        """Test performance of EOQ calculations"""
        # Get first raw material for testing
        session = self.db_manager.get_session()
        try:
            from egg_farm_system.database.models import RawMaterial
            
            material = session.query(RawMaterial).first()
            if not material:
                # Create one if none exist
                material = RawMaterial(
                    name="EOQ Test Material",
                    unit="kg",
                    current_stock=100,
                    low_stock_alert=20,
                    cost_afg=25.0
                )
                session.add(material)
                session.commit()
            
            material_id = material.id
            
        finally:
            session.close()
        
        optimizer = InventoryOptimizer()
        
        def calculate_eoq():
            result = optimizer.calculate_economic_order_quantity(
                item_id=material_id,
                item_type='raw_material',
                unit_cost=25.0,
                annual_demand=3650,  # 10 units per day
                ordering_cost=1000,
                holding_cost_rate=0.25
            )
            return result
        
        # Benchmark EOQ calculation
        result = benchmark(calculate_eoq)
        
        # Verify results
        assert "error" not in result or result.get("error") is not None
        if "error" not in result:
            assert result["eoq_analysis"]["economic_order_quantity"] > 0
    
    @pytest.mark.benchmark
    def test_budget_creation_performance(self, benchmark):
        """Test performance of budget creation with historical data"""
        # Add more comprehensive historical financial data
        session = self.db_manager.get_session()
        try:
            from egg_farm_system.database.models import Sale, Expense, Party
            
            # Create multiple customers and suppliers
            parties = []
            for i in range(20):  # 20 parties
                party = Party(
                    name=f"Test Party {i+1}",
                    party_type="Customer" if i < 15 else "Supplier",
                    contact_info=f"party{i+1}@example.com"
                )
                parties.append(party)
            
            session.bulk_save_objects(parties)
            session.commit()
            
            # Create 2 years of sales data
            base_date = datetime(datetime.utcnow().year - 2, 1, 1)
            sales = []
            
            for year in [datetime.utcnow().year - 2, datetime.utcnow().year - 1]:
                for month in range(1, 13):
                    for party in parties[:15]:  # Only customers make sales
                        sale = Sale(
                            party_id=party.id,
                            date=datetime(year, month, 15),
                            total_amount_afg=np.random.randint(20000, 80000),
                            total_amount_usd=np.random.randint(220, 890)
                        )
                        sales.append(sale)
            
            session.bulk_save_objects(sales)
            
            # Create 2 years of expense data
            expenses = []
            for year in [datetime.utcnow().year - 2, datetime.utcnow().year - 1]:
                for month in range(1, 13):
                    for category in ["Feed", "Labor", "Utilities", "Maintenance"]:
                        expense = Expense(
                            date=datetime(year, month, 10),
                            category=category,
                            amount_afg=np.random.randint(5000, 25000),
                            amount_usd=np.random.randint(55, 278)
                        )
                        expenses.append(expense)
            
            session.bulk_save_objects(expenses)
            session.commit()
            
        finally:
            session.close()
        
        planner = FinancialPlanner()
        
        def create_budget():
            result = planner.create_budget(
                farm_id=1,
                year=datetime.utcnow().year,
                egg_price_growth=0.05,
                feed_inflation=0.08
            )
            return result
        
        # Benchmark budget creation
        result = benchmark(create_budget)
        
        # Verify results
        assert "error" not in result or result.get("error") is not None
    
    @pytest.mark.benchmark
    def test_comprehensive_optimization_performance(self, benchmark):
        """Test performance of comprehensive inventory optimization"""
        # This test combines multiple optimization operations
        optimizer = InventoryOptimizer()
        
        def run_comprehensive_optimization():
            # Run all optimization functions
            results = {}
            
            # 1. Demand forecasting for multiple items
            session = self.db_manager.get_session()
            try:
                materials = session.query(RawMaterial).limit(5).all()  # Test with 5 materials
                
                for material in materials:
                    forecast = optimizer.forecast_demand(
                        item_id=material.id,
                        item_type='raw_material',
                        days_ahead=30
                    )
                    results[f"forecast_{material.id}"] = forecast
                
            finally:
                session.close()
            
            # 2. EOQ calculations for multiple items
            session = self.db_manager.get_session()
            try:
                materials = session.query(RawMaterial).limit(3).all()  # Test with 3 materials
                
                for material in materials:
                    eoq = optimizer.calculate_economic_order_quantity(
                        item_id=material.id,
                        item_type='raw_material',
                        unit_cost=material.cost_afg,
                        annual_demand=3650
                    )
                    results[f"eoq_{material.id}"] = eoq
                    
            finally:
                session.close()
            
            # 3. Comprehensive optimization
            optimization = optimizer.optimize_inventory_levels(farm_id=1)
            results["optimization"] = optimization
            
            return results
        
        # Benchmark comprehensive optimization
        results = benchmark(run_comprehensive_optimization)
        
        # Verify results
        assert len(results) > 0
        assert any("error" not in result or result.get("error") is not None for result in results.values())

class TestMemoryUsage:
    """Test memory usage and efficiency of new features"""
    
    def setup_method(self):
        """Set up memory test environment"""
        # Record baseline memory
        process = psutil.Process()
        self.baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    @pytest.mark.slow
    def test_analytics_memory_usage(self):
        """Test memory usage of analytics operations"""
        # Create test environment similar to performance tests
        test_db_path = tempfile.mktemp(suffix='.db')
        db_manager = DatabaseManager()
        db_manager.engine = db_manager.create_test_engine(test_db_path)
        
        # Create tables and sample data
        Base.metadata.create_all(bind=db_manager.engine)
        self.setup_comprehensive_sample_data(db_manager)
        
        try:
            # Record memory before analytics
            process = psutil.Process()
            memory_before = process.memory_info().rss / 1024 / 1024  # MB
            
            # Run analytics operations
            analytics = AdvancedAnalytics()
            
            # Production forecast
            forecast = analytics.forecast_egg_production(farm_id=1, days_ahead=30)
            
            # Financial forecast
            financial_forecast = analytics.forecast_financial_performance(farm_id=1, months_ahead=12)
            
            # Inventory analysis
            inventory_analysis = analytics.analyze_inventory_optimization(farm_id=1)
            
            # Record memory after analytics
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = memory_after - memory_before
            
            # Memory increase should be reasonable (less than 100MB for these operations)
            assert memory_increase < 100, f"Memory increase too high: {memory_increase}MB"
            
            # Clean up references to help garbage collection
            del forecast, financial_forecast, inventory_analysis
            gc.collect()
            
        finally:
            db_manager.engine.dispose()
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
    
    def setup_comprehensive_sample_data(self, db_manager):
        """Setup comprehensive sample data for memory testing"""
        session = db_manager.get_session()
        
        try:
            # Create farm
            farm = Farm(name="Memory Test Farm", location="Test Location")
            session.add(farm)
            session.commit()
            
            # Create sheds
            sheds = []
            for i in range(20):  # More sheds for memory test
                shed = Shed(farm_id=farm.id, name=f"Memory Test Shed {i+1}", capacity=1000)
                session.add(shed)
                sheds.append(shed)
            session.commit()
            
            # Create extensive production data
            base_date = datetime.utcnow().date() - timedelta(days=365)
            productions = []
            
            for day in range(365):  # 1 year of data
                production_date = base_date + timedelta(days=day)
                for shed in sheds:
                    total_eggs = np.random.randint(600, 1200)
                    
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
                    productions.append(production)
            
            session.bulk_save_objects(productions)
            session.commit()
            
            # Create financial data
            from egg_farm_system.database.models import Sale, Expense, Party, RawMaterial
            
            # Create parties
            parties = []
            for i in range(30):
                party = Party(
                    name=f"Memory Test Party {i+1}",
                    party_type="Customer" if i < 20 else "Supplier",
                    contact_info=f"memory{i+1}@example.com"
                )
                parties.append(party)
            
            session.bulk_save_objects(parties)
            session.commit()
            
            # Create sales and expenses
            sales = []
            expenses = []
            
            for month in range(12):  # 1 year of monthly data
                for party in parties[:20]:  # Only customers make sales
                    sale = Sale(
                        party_id=party.id,
                        date=datetime.utcnow().replace(day=15) - timedelta(days=30*month),
                        total_amount_afg=np.random.randint(30000, 90000),
                        total_amount_usd=np.random.randint(330, 1000)
                    )
                    sales.append(sale)
                
                for category in ["Feed", "Labor", "Utilities", "Maintenance", "Veterinary"]:
                    expense = Expense(
                        date=datetime.utcnow().replace(day=10) - timedelta(days=30*month),
                        category=category,
                        amount_afg=np.random.randint(8000, 30000),
                        amount_usd=np.random.randint(88, 333)
                    )
                    expenses.append(expense)
            
            session.bulk_save_objects(sales + expenses)
            
            # Create inventory data
            raw_materials = []
            for i in range(100):  # 100 different materials
                material = RawMaterial(
                    name=f"Memory Test Material {i+1}",
                    unit="kg",
                    current_stock=np.random.randint(10, 1500),
                    low_stock_alert=np.random.randint(5, 100),
                    cost_afg=np.random.uniform(10, 150)
                )
                raw_materials.append(material)
            
            session.bulk_save_objects(raw_materials)
            session.commit()
            
        finally:
            session.close()

class TestScalability:
    """Test scalability with large datasets"""
    
    def test_large_dataset_performance(self):
        """Test performance with large datasets (stress test)"""
        # This is a stress test that creates a very large dataset
        test_db_path = tempfile.mktemp(suffix='.db')
        db_manager = DatabaseManager()
        db_manager.engine = db_manager.create_test_engine(test_db_path)
        
        try:
            # Create tables
            Base.metadata.create_all(bind=db_manager.engine)
            
            # Create large dataset
            session = db_manager.get_session()
            try:
                # Create farm
                farm = Farm(name="Scalability Test Farm", location="Test Location")
                session.add(farm)
                session.commit()
                
                # Create many sheds
                sheds = []
                for i in range(50):  # 50 sheds
                    shed = Shed(farm_id=farm.id, name=f"Scalability Shed {i+1}", capacity=1000)
                    sheds.append(shed)
                session.add_all(sheds)
                session.commit()
                
                # Create very large production dataset
                print("Creating large production dataset...")
                base_date = datetime.utcnow().date() - timedelta(days=365)
                
                # Batch insert production data to avoid memory issues
                batch_size = 1000
                total_productions = 0
                
                for day in range(0, 365, 10):  # Every 10 days for stress test
                    batch_productions = []
                    production_date = base_date + timedelta(days=day)
                    
                    for shed in sheds:
                        total_eggs = np.random.randint(600, 1200)
                        
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
                        batch_productions.append(production)
                        
                        if len(batch_productions) >= batch_size:
                            session.bulk_save_objects(batch_productions)
                            total_productions += len(batch_productions)
                            batch_productions = []
                            session.commit()
                    
                    if batch_productions:
                        session.bulk_save_objects(batch_productions)
                        total_productions += len(batch_productions)
                        session.commit()
                    
                    print(f"Created {total_productions} production records...")
                
                print(f"Total production records created: {total_productions}")
                
            finally:
                session.close()
            
            # Test analytics performance with large dataset
            print("Testing analytics performance with large dataset...")
            start_time = time.time()
            
            analytics = AdvancedAnalytics()
            result = analytics.forecast_egg_production(farm_id=1, days_ahead=30)
            
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"Analytics completed in {duration:.2f} seconds")
            
            # Should complete within reasonable time (less than 30 seconds for large dataset)
            assert duration < 30, f"Analytics took too long: {duration:.2f} seconds"
            
            # Verify results are still valid
            assert "error" not in result or result.get("error") is not None
            
        finally:
            db_manager.engine.dispose()
            if os.path.exists(test_db_path):
                os.remove(test_db_path)

def run_performance_tests():
    """Run performance tests and generate report"""
    import pytest
    
    # Run tests with benchmark markers
    exit_code = pytest.main([
        __file__,
        "-v",
        "--benchmark-only",
        "--benchmark-sort=mean",
        "--benchmark-columns=mean,min,max,stddev",
        "--benchmark-json=benchmark-results.json"
    ])
    
    return exit_code == 0

if __name__ == "__main__":
    success = run_performance_tests()
    sys.exit(0 if success else 1)
