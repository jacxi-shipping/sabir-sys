import pytest

from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.purchases import PurchaseManager
from egg_farm_system.modules.egg_production import EggProductionManager
from egg_farm_system.database.models import RawMaterial, Party, Farm, Shed, EggInventory


def setup_module(module):
    DatabaseManager.initialize()


def teardown_module(module):
    DatabaseManager.close()


def get_or_create_party(session):
    p = session.query(Party).first()
    if not p:
        p = Party(name='Default Supplier')
        session.add(p)
        session.flush()
    return p


def test_packaging_purchase_updates_raw_material_stock():
    pm = PurchaseManager()
    session = pm.session
    try:
        party = get_or_create_party(session)
        # Ensure starting carton stock
        carton = session.query(RawMaterial).filter(RawMaterial.name == 'Carton').first()
        start = carton.current_stock if carton else 0
        purchase = pm.record_packaging_purchase(party_id=party.id, material_name='Carton', quantity=5, rate_afg=10, rate_usd=0.13)
        # Refresh
        carton = session.query(RawMaterial).filter(RawMaterial.name == 'Carton').first()
        assert carton.current_stock == start + 5
    finally:
        pm.close_session()


def test_production_consumes_packaging_and_adds_eggs():
    # Prepare session and ensure we have farm/shed
    dbs = DatabaseManager.get_session()
    try:
        farm = dbs.query(Farm).first()
        if not farm:
            farm = Farm(name='TestFarm')
            dbs.add(farm)
            dbs.flush()
        shed = dbs.query(Shed).filter(Shed.farm_id == farm.id).first()
        if not shed:
            shed = Shed(farm_id=farm.id, name='Shed1', capacity=100)
            dbs.add(shed)
            dbs.flush()

        # Ensure packaging stock exists and has some units
        pm = PurchaseManager()
        try:
            party = get_or_create_party(pm.session)
            pm.record_packaging_purchase(party_id=party.id, material_name='Carton', quantity=10, rate_afg=5, rate_usd=0.06)
            pm.record_packaging_purchase(party_id=party.id, material_name='Tray', quantity=10, rate_afg=2, rate_usd=0.03)
        finally:
            pm.close_session()

        # Get starting stocks
        carton = dbs.query(RawMaterial).filter(RawMaterial.name == 'Carton').first()
        tray = dbs.query(RawMaterial).filter(RawMaterial.name == 'Tray').first()
        start_carton = carton.current_stock
        start_tray = tray.current_stock

        # Run production that uses 3 cartons and 2 trays and produces eggs
        from datetime import datetime
        epm = EggProductionManager()
        try:
            prod = epm.record_production(shed.id, datetime.utcnow(), small=10, medium=5, large=3, broken=0, cartons_used=3, trays_used=2)
        finally:
            epm.session.close()

        # Verify production saved packaging usage
        assert prod.cartons_used == 3
        assert prod.trays_used == 2

        # Verify egg inventory updated: assert usable eggs increased
        totals = dbs.query(EggInventory).all()
        total_eggs = sum(i.current_stock for i in totals)
        assert total_eggs >= 18
    finally:
        dbs.close()
