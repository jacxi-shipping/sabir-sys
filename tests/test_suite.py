"""Modernized core tests aligned with current schema and manager behavior."""

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from egg_farm_system.database.db import Base, DatabaseManager
from egg_farm_system.database.models import (
    EggGrade,
    EggInventory,
    Farm,
    Party,
    RawMaterial,
    Shed,
)
from egg_farm_system.modules.egg_production import EggProductionManager
from egg_farm_system.modules.ledger import LedgerManager
from egg_farm_system.modules.purchases import PurchaseManager
from egg_farm_system.modules.sales import SalesManager
from egg_farm_system.utils.time_utils import utcnow_naive


@pytest.fixture
def db_session():
    """Provide isolated in-memory DB and wire DatabaseManager to it."""
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
        yield session
    finally:
        session.close()
        engine.dispose()
        DatabaseManager._engine = None
        DatabaseManager._SessionLocal = None


def _create_farm_and_shed(session):
    farm = Farm(name="Test Farm", location="Test Location")
    session.add(farm)
    session.flush()

    shed = Shed(farm_id=farm.id, name="Shed A", capacity=1000)
    session.add(shed)
    session.commit()
    return farm, shed


def _create_party(session, name="Test Party"):
    party = Party(name=name, phone="0700000000", address="Kabul")
    session.add(party)
    session.commit()
    return party


def _ensure_material(session, name="Corn"):
    material = RawMaterial(name=name, unit="kg", current_stock=0)
    session.add(material)
    session.commit()
    return material


def _ensure_egg_stock(session, large=0, medium=0, small=0):
    for grade, qty in [
        (EggGrade.LARGE, large),
        (EggGrade.MEDIUM, medium),
        (EggGrade.SMALL, small),
    ]:
        row = EggInventory(grade=grade, current_stock=qty)
        session.add(row)
    session.commit()


def test_egg_production_updates_inventory_and_packaging(db_session):
    farm, shed = _create_farm_and_shed(db_session)

    carton = RawMaterial(farm_id=farm.id, name="Carton", unit="pcs", current_stock=10)
    tray = RawMaterial(farm_id=farm.id, name="Tray", unit="pcs", current_stock=10)
    db_session.add_all([carton, tray])
    db_session.commit()

    with EggProductionManager() as manager:
        prod = manager.record_production(
            shed_id=shed.id,
            date=utcnow_naive(),
            small=5,
            medium=3,
            large=2,
            broken=1,
            cartons_used=2,
            trays_used=1,
        )

    db_session.expire_all()

    assert prod.total_eggs == 11
    assert prod.usable_eggs == 10

    stocks = {row.grade: row.current_stock for row in db_session.query(EggInventory).all()}
    assert stocks[EggGrade.SMALL] == 5
    assert stocks[EggGrade.MEDIUM] == 3
    assert stocks[EggGrade.LARGE] == 2

    refreshed_carton = db_session.query(RawMaterial).filter(RawMaterial.name == "Carton").first()
    refreshed_tray = db_session.query(RawMaterial).filter(RawMaterial.name == "Tray").first()
    assert refreshed_carton.current_stock == 8
    assert refreshed_tray.current_stock == 9


def test_purchase_credit_updates_stock_and_negative_balance(db_session):
    party = _create_party(db_session, name="Supplier A")
    material = _ensure_material(db_session, name="Soybean")

    with PurchaseManager() as manager:
        manager.record_purchase(
            party_id=party.id,
            material_id=material.id,
            quantity=10,
            rate_afg=100,
            rate_usd=1.28,
            payment_method="Credit",
        )

    db_session.expire_all()

    refreshed = db_session.query(RawMaterial).filter(RawMaterial.id == material.id).first()
    assert refreshed.current_stock == 10
    assert refreshed.total_quantity_purchased == 10
    assert refreshed.total_cost_purchased_afg == 1000

    balance_afg = LedgerManager().get_party_balance(party.id, "AFG")
    assert balance_afg == pytest.approx(-1000)


def test_purchase_cash_offsets_balance_to_zero(db_session):
    party = _create_party(db_session, name="Supplier Cash")
    material = _ensure_material(db_session, name="Wheat")

    with PurchaseManager() as manager:
        manager.record_purchase(
            party_id=party.id,
            material_id=material.id,
            quantity=5,
            rate_afg=100,
            rate_usd=1.28,
            payment_method="Cash",
        )

    balance_afg = LedgerManager().get_party_balance(party.id, "AFG")
    balance_usd = LedgerManager().get_party_balance(party.id, "USD")
    assert balance_afg == pytest.approx(0)
    assert balance_usd == pytest.approx(0)


def test_sales_credit_consumes_inventory_and_positive_balance(db_session):
    party = _create_party(db_session, name="Customer Credit")
    _ensure_egg_stock(db_session, large=30, medium=0, small=0)

    with SalesManager() as manager:
        manager.record_sale(
            party_id=party.id,
            quantity=12,
            rate_afg=50,
            rate_usd=0.64,
            payment_method="Credit",
        )

    large_stock = db_session.query(EggInventory).filter(EggInventory.grade == EggGrade.LARGE).first()
    assert large_stock.current_stock == 18

    balance_afg = LedgerManager().get_party_balance(party.id, "AFG")
    assert balance_afg == pytest.approx(600)


def test_sales_cash_offsets_balance_to_zero(db_session):
    party = _create_party(db_session, name="Customer Cash")
    _ensure_egg_stock(db_session, large=20, medium=0, small=0)

    with SalesManager() as manager:
        manager.record_sale(
            party_id=party.id,
            quantity=10,
            rate_afg=40,
            rate_usd=0.51,
            payment_method="Cash",
        )

    balance_afg = LedgerManager().get_party_balance(party.id, "AFG")
    balance_usd = LedgerManager().get_party_balance(party.id, "USD")
    assert balance_afg == pytest.approx(0)
    assert balance_usd == pytest.approx(0)

