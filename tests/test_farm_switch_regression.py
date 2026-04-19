"""Regression tests for farm-scoped switching behavior."""

from datetime import datetime

import pytest

from egg_farm_system.database.models import (
    EggGrade,
    EggInventory,
    Farm,
    FeedType,
    FinishedFeed,
    Party,
    RawMaterial,
)
from egg_farm_system.modules.expenses import ExpenseManager
from egg_farm_system.modules.inventory import InventoryManager
from egg_farm_system.modules.ledger import LedgerManager
from egg_farm_system.modules.purchases import PurchaseManager
from egg_farm_system.modules.sales import SalesManager


def _seed_base(session):
    farm1 = Farm(name="Farm A", location="Loc A")
    farm2 = Farm(name="Farm B", location="Loc B")
    party = Party(name="Common Party")
    session.add_all([farm1, farm2, party])
    session.commit()
    return farm1, farm2, party


def test_inventory_manager_scopes_by_farm(isolated_db):
    session = isolated_db()
    farm1, farm2, _ = _seed_base(session)

    session.add_all(
        [
            RawMaterial(farm_id=farm1.id, name="Corn", unit="kg", current_stock=100, total_quantity_purchased=100, total_cost_purchased_afg=1000, total_cost_purchased_usd=10),
            RawMaterial(farm_id=farm2.id, name="Corn", unit="kg", current_stock=200, total_quantity_purchased=200, total_cost_purchased_afg=2200, total_cost_purchased_usd=22),
            FinishedFeed(farm_id=farm1.id, feed_type=FeedType.LAYER, current_stock=30, cost_per_kg_afg=20, cost_per_kg_usd=0.25),
            FinishedFeed(farm_id=farm2.id, feed_type=FeedType.LAYER, current_stock=50, cost_per_kg_afg=25, cost_per_kg_usd=0.32),
            EggInventory(farm_id=farm1.id, grade=EggGrade.LARGE, current_stock=40),
            EggInventory(farm_id=farm2.id, grade=EggGrade.LARGE, current_stock=90),
        ]
    )
    session.commit()

    manager = InventoryManager()

    farm1_materials = manager.get_raw_materials_inventory(farm_id=farm1.id)
    farm2_materials = manager.get_raw_materials_inventory(farm_id=farm2.id)

    assert len(farm1_materials) == 1
    assert len(farm2_materials) == 1
    assert farm1_materials[0]["stock"] == 100
    assert farm2_materials[0]["stock"] == 200

    farm1_totals = manager.get_total_inventory_value(farm_id=farm1.id)
    farm2_totals = manager.get_total_inventory_value(farm_id=farm2.id)
    assert farm1_totals["total_afg"] != farm2_totals["total_afg"]


def test_sales_purchases_expenses_scoped_queries(isolated_db):
    session = isolated_db()
    farm1, farm2, party = _seed_base(session)

    m1 = RawMaterial(farm_id=farm1.id, name="Soy", unit="kg", current_stock=500, total_quantity_purchased=500, total_cost_purchased_afg=5000, total_cost_purchased_usd=60)
    m2 = RawMaterial(farm_id=farm2.id, name="Soy", unit="kg", current_stock=500, total_quantity_purchased=500, total_cost_purchased_afg=5000, total_cost_purchased_usd=60)
    session.add_all([m1, m2])
    session.add_all(
        [
            EggInventory(farm_id=farm1.id, grade=EggGrade.LARGE, current_stock=300),
            EggInventory(farm_id=farm2.id, grade=EggGrade.LARGE, current_stock=300),
        ]
    )
    session.commit()

    with SalesManager() as sm:
        sm.record_sale(party_id=party.id, quantity=30, rate_afg=5, rate_usd=0.06, payment_method="Credit", farm_id=farm1.id)
        sm.record_sale(party_id=party.id, quantity=20, rate_afg=6, rate_usd=0.07, payment_method="Credit", farm_id=farm2.id)

    with PurchaseManager() as pm:
        pm.record_purchase(party_id=party.id, material_id=m1.id, quantity=10, rate_afg=100, rate_usd=1.2, payment_method="Credit", farm_id=farm1.id)
        pm.record_purchase(party_id=party.id, material_id=m2.id, quantity=8, rate_afg=110, rate_usd=1.3, payment_method="Credit", farm_id=farm2.id)

    with ExpenseManager() as em:
        em.record_expense(farm_id=farm1.id, category="Fuel", amount_afg=150, amount_usd=2, party_id=party.id, payment_method="Credit")
        em.record_expense(farm_id=farm2.id, category="Fuel", amount_afg=350, amount_usd=4, party_id=party.id, payment_method="Credit")

    with SalesManager() as sm:
        f1_sales = sm.get_sales(farm_id=farm1.id)
        f2_sales = sm.get_sales(farm_id=farm2.id)
        assert len(f1_sales) == 1
        assert len(f2_sales) == 1
        assert f1_sales[0].total_afg != f2_sales[0].total_afg

    with PurchaseManager() as pm:
        f1_purchases = pm.get_purchases(farm_id=farm1.id)
        f2_purchases = pm.get_purchases(farm_id=farm2.id)
        assert len(f1_purchases) == 1
        assert len(f2_purchases) == 1
        assert f1_purchases[0].material_id != f2_purchases[0].material_id

    with ExpenseManager() as em:
        f1_expenses = em.get_expenses(farm_id=farm1.id)
        f2_expenses = em.get_expenses(farm_id=farm2.id)
        assert len(f1_expenses) == 1
        assert len(f2_expenses) == 1
        assert f1_expenses[0].amount_afg != f2_expenses[0].amount_afg


def test_ledger_balances_scoped_by_farm(isolated_db):
    session = isolated_db()
    farm1, farm2, party = _seed_base(session)

    ledger = LedgerManager()
    s = isolated_db()
    try:
        ledger.post_entry(
            party_id=party.id,
            farm_id=farm1.id,
            date=datetime.now(),
            description="Farm1 Debit",
            debit_afg=100,
            session=s,
        )
        ledger.post_entry(
            party_id=party.id,
            farm_id=farm2.id,
            date=datetime.now(),
            description="Farm2 Credit",
            credit_afg=40,
            session=s,
        )
        s.commit()
    finally:
        s.close()

    f1_balance = ledger.get_party_balance(party.id, "AFG", farm_id=farm1.id)
    f2_balance = ledger.get_party_balance(party.id, "AFG", farm_id=farm2.id)
    all_balance = ledger.get_party_balance(party.id, "AFG")

    assert f1_balance == pytest.approx(100)
    assert f2_balance == pytest.approx(-40)
    assert all_balance == pytest.approx(60)
