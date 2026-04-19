"""Performance benchmarks aligned with the current schema.

These tests are intended for the optional benchmark CI job.
"""

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from egg_farm_system.database.db import Base, DatabaseManager
from egg_farm_system.database.models import (
    EggProduction,
    Expense,
    Farm,
    FeedType,
    FinishedFeed,
    Party,
    Purchase,
    RawMaterial,
    Sale,
    Shed,
)
from egg_farm_system.modules.advanced_analytics import AdvancedAnalytics
from egg_farm_system.modules.inventory_optimizer import InventoryOptimizer
from egg_farm_system.utils.time_utils import utcnow_naive


@pytest.fixture(scope="module")
def perf_db():
    """Create an isolated in-memory database with realistic benchmark fixtures."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)
    Base.metadata.create_all(bind=engine)

    DatabaseManager._engine = engine
    DatabaseManager._SessionLocal = SessionLocal

    session = SessionLocal()
    try:
        # Farm + sheds
        farm = Farm(name="Perf Farm", location="Benchmark")
        session.add(farm)
        session.flush()

        sheds = []
        for i in range(6):
            shed = Shed(farm_id=farm.id, name=f"Shed-{i+1}", capacity=1200)
            session.add(shed)
            sheds.append(shed)
        session.flush()

        # Parties
        customer = Party(name="Perf Customer", phone="0700000001", address="Kabul")
        supplier = Party(name="Perf Supplier", phone="0700000002", address="Kabul")
        session.add_all([customer, supplier])
        session.flush()

        # Raw materials
        materials = []
        for i in range(20):
            qty = float(np.random.randint(200, 1000))
            afg = qty * float(np.random.uniform(20, 60))
            usd = afg / 78.0
            rm = RawMaterial(
                name=f"Material-{i+1}",
                unit="kg",
                current_stock=qty,
                total_quantity_purchased=qty,
                total_cost_purchased_afg=afg,
                total_cost_purchased_usd=usd,
                low_stock_alert=50,
                supplier_id=supplier.id,
            )
            session.add(rm)
            materials.append(rm)
        session.flush()

        # Finished feeds
        feed_types = [FeedType.STARTER, FeedType.GROWER, FeedType.LAYER]
        for i in range(6):
            ff = FinishedFeed(
                feed_type=feed_types[i % 3],
                current_stock=float(np.random.randint(100, 500)),
                cost_per_kg_afg=float(np.random.uniform(25, 55)),
                cost_per_kg_usd=float(np.random.uniform(0.3, 0.8)),
                low_stock_alert=80,
            )
            session.add(ff)
        session.flush()

        # Production history (180 days)
        base_date = utcnow_naive().date() - timedelta(days=180)
        prod_rows = []
        for day in range(180):
            d = base_date + timedelta(days=day)
            for shed in sheds:
                total = int(max(0, np.random.normal(850, 80)))
                broken = int(total * 0.03)
                usable = total - broken
                small = int(usable * 0.25)
                medium = int(usable * 0.45)
                large = usable - small - medium
                prod_rows.append(
                    EggProduction(
                        shed_id=shed.id,
                        date=datetime.combine(d, datetime.min.time()),
                        small_count=small,
                        medium_count=medium,
                        large_count=large,
                        broken_count=broken,
                    )
                )
        session.bulk_save_objects(prod_rows)

        # Sales / purchases / expenses history
        sales_rows = []
        purchase_rows = []
        expense_rows = []
        for day in range(120):
            d = utcnow_naive() - timedelta(days=day)
            qty = int(np.random.randint(200, 800))
            rate_afg = float(np.random.uniform(4.5, 6.5))
            rate_usd = rate_afg / 78.0
            total_afg = qty * rate_afg
            total_usd = qty * rate_usd

            sales_rows.append(
                Sale(
                    party_id=customer.id,
                    farm_id=farm.id,
                    date=d,
                    quantity=qty,
                    rate_afg=rate_afg,
                    rate_usd=rate_usd,
                    total_afg=total_afg,
                    total_usd=total_usd,
                    exchange_rate_used=78.0,
                    payment_method="Credit",
                )
            )

            mat = materials[day % len(materials)]
            p_qty = float(np.random.uniform(20, 120))
            p_rate_afg = float(np.random.uniform(20, 55))
            p_rate_usd = p_rate_afg / 78.0
            purchase_rows.append(
                Purchase(
                    party_id=supplier.id,
                    farm_id=farm.id,
                    material_id=mat.id,
                    date=d,
                    quantity=p_qty,
                    rate_afg=p_rate_afg,
                    rate_usd=p_rate_usd,
                    total_afg=p_qty * p_rate_afg,
                    total_usd=p_qty * p_rate_usd,
                    exchange_rate_used=78.0,
                    payment_method="Credit",
                )
            )

            expense_rows.append(
                Expense(
                    farm_id=farm.id,
                    party_id=supplier.id,
                    date=d,
                    category="Feed",
                    description="Benchmark expense",
                    amount_afg=float(np.random.uniform(2000, 8000)),
                    amount_usd=float(np.random.uniform(25, 110)),
                    exchange_rate_used=78.0,
                    payment_method="Cash",
                )
            )

        session.bulk_save_objects(sales_rows)
        session.bulk_save_objects(purchase_rows)
        session.bulk_save_objects(expense_rows)
        session.commit()

        yield {
            "farm_id": farm.id,
            "material_id": materials[0].id,
        }
    finally:
        session.close()
        engine.dispose()
        DatabaseManager._engine = None
        DatabaseManager._SessionLocal = None


@pytest.mark.benchmark
def test_production_forecast_benchmark(perf_db, benchmark):
    analytics = AdvancedAnalytics()

    def run():
        return analytics.forecast_egg_production(farm_id=perf_db["farm_id"], days_ahead=30)

    result = benchmark(run)
    assert "error" not in result
    assert "forecasts" in result


@pytest.mark.benchmark
def test_inventory_analysis_benchmark(perf_db, benchmark):
    analytics = AdvancedAnalytics()

    def run():
        return analytics.analyze_inventory_optimization(farm_id=perf_db["farm_id"])

    result = benchmark(run)
    assert "error" not in result
    assert "abc_analysis" in result


@pytest.mark.benchmark
def test_demand_forecast_benchmark(perf_db, benchmark):
    optimizer = InventoryOptimizer()

    def run():
        return optimizer.forecast_demand(
            item_id=perf_db["material_id"],
            item_type="raw_material",
            days_ahead=30,
        )

    result = benchmark(run)
    assert "error" not in result
    assert "ensemble_forecast" in result


@pytest.mark.benchmark
def test_eoq_benchmark(perf_db, benchmark):
    optimizer = InventoryOptimizer()

    def run():
        return optimizer.calculate_economic_order_quantity(
            item_id=perf_db["material_id"],
            item_type="raw_material",
            annual_demand=3650,
            ordering_cost=1200,
            holding_cost_rate=0.25,
        )

    result = benchmark(run)
    assert "error" not in result
    assert "eoq_analysis" in result

