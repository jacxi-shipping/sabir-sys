"""Pytest-style cash/credit balance behavior tests."""

from datetime import UTC, datetime

import pytest

from egg_farm_system.database.models import EggGrade, EggInventory, RawMaterial
from egg_farm_system.modules.ledger import LedgerManager
from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.modules.purchases import PurchaseManager
from egg_farm_system.modules.sales import SalesManager
from egg_farm_system.utils.time_utils import utcnow_naive


def _make_party(tag: str):
    manager = PartyManager()
    return manager.create_party(
        name=f"{tag} {utcnow_naive().timestamp()}",
        phone="1234567890",
        address="Test Address",
    )


def _ensure_material(session, name="Test Material"):
    material = session.query(RawMaterial).filter(RawMaterial.name == name).first()
    if not material:
        material = RawMaterial(name=name, unit="kg", current_stock=0)
        session.add(material)
        session.commit()
    return material


def _seed_egg_inventory(session, large=300, medium=200, small=100):
    rows = [
        (EggGrade.LARGE, large),
        (EggGrade.MEDIUM, medium),
        (EggGrade.SMALL, small),
    ]
    for grade, qty in rows:
        stock = session.query(EggInventory).filter(EggInventory.grade == grade).first()
        if not stock:
            stock = EggInventory(grade=grade, current_stock=0)
            session.add(stock)
            session.flush()
        stock.current_stock = max(stock.current_stock or 0, qty)
        session.add(stock)
    session.commit()


def test_cash_sale_balance_zero(isolated_db):
    session = isolated_db()
    _seed_egg_inventory(session)
    party = _make_party("Cash Sale Party")

    with SalesManager() as sales_manager:
        sales_manager.record_sale(
            party_id=party.id,
            quantity=100,
            rate_afg=50.0,
            rate_usd=0.64,
            payment_method="Cash",
        )

    ledger_manager = LedgerManager()
    assert ledger_manager.get_party_balance(party.id, "AFG") == pytest.approx(0)
    assert ledger_manager.get_party_balance(party.id, "USD") == pytest.approx(0)


def test_credit_sale_balance_positive(isolated_db):
    session = isolated_db()
    _seed_egg_inventory(session)
    party = _make_party("Credit Sale Party")

    with SalesManager() as sales_manager:
        sales_manager.record_sale(
            party_id=party.id,
            quantity=200,
            rate_afg=50.0,
            rate_usd=0.64,
            payment_method="Credit",
        )

    ledger_manager = LedgerManager()
    assert ledger_manager.get_party_balance(party.id, "AFG") == pytest.approx(10000)
    assert ledger_manager.get_party_balance(party.id, "USD") == pytest.approx(128)


def test_cash_purchase_balance_zero(isolated_db):
    session = isolated_db()
    party = _make_party("Cash Purchase Party")
    material = _ensure_material(session)

    with PurchaseManager() as purchase_manager:
        purchase_manager.record_purchase(
            party_id=party.id,
            material_id=material.id,
            quantity=50,
            rate_afg=100.0,
            rate_usd=1.28,
            payment_method="Cash",
        )

    ledger_manager = LedgerManager()
    assert ledger_manager.get_party_balance(party.id, "AFG") == pytest.approx(0)
    assert ledger_manager.get_party_balance(party.id, "USD") == pytest.approx(0)


def test_credit_purchase_balance_negative(isolated_db):
    session = isolated_db()
    party = _make_party("Credit Purchase Party")
    material = _ensure_material(session)

    with PurchaseManager() as purchase_manager:
        purchase_manager.record_purchase(
            party_id=party.id,
            material_id=material.id,
            quantity=75,
            rate_afg=100.0,
            rate_usd=1.28,
            payment_method="Credit",
        )

    ledger_manager = LedgerManager()
    assert ledger_manager.get_party_balance(party.id, "AFG") == pytest.approx(-7500)
    assert ledger_manager.get_party_balance(party.id, "USD") == pytest.approx(-96)

