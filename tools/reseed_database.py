"""Reset and reseed the application database with coherent demo data."""

from datetime import datetime, timedelta
from pathlib import Path
import shutil
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from egg_farm_system.config import DB_PATH
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.database.models import (
    EggGrade,
    EggInventory,
    EggProduction,
    Expense,
    Farm,
    Party,
    Payment,
    Purchase,
    RawMaterial,
    Sale,
    Shed,
)
from egg_farm_system.modules.users import UserManager
from egg_farm_system.utils.time_utils import utcnow_naive


def reset_database_file() -> Path | None:
    """Backup current DB and remove it to force a clean rebuild."""
    if not DB_PATH.exists():
        return None

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = DB_PATH.with_name(f"{DB_PATH.stem}.backup_{stamp}{DB_PATH.suffix}")
    shutil.copy2(DB_PATH, backup_path)
    DB_PATH.unlink()
    return backup_path


def seed_data() -> dict:
    DatabaseManager.initialize()
    session = DatabaseManager.get_session()

    try:
        now = utcnow_naive()
        ex_rate = 78.0

        # Farms and sheds
        farm_a = Farm(name="North Farm", location="District 1")
        farm_b = Farm(name="South Farm", location="District 2")
        session.add_all([farm_a, farm_b])
        session.flush()

        sheds = [
            Shed(farm_id=farm_a.id, name="North Shed A", capacity=1800),
            Shed(farm_id=farm_a.id, name="North Shed B", capacity=1500),
            Shed(farm_id=farm_b.id, name="South Shed A", capacity=1700),
            Shed(farm_id=farm_b.id, name="South Shed B", capacity=1400),
        ]
        session.add_all(sheds)
        session.flush()

        # Parties
        supplier_a = Party(name="Supplier North", phone="0700000101", address="Kabul")
        supplier_b = Party(name="Supplier South", phone="0700000102", address="Kandahar")
        customer_a = Party(name="Customer North", phone="0700000201", address="Kabul")
        customer_b = Party(name="Customer South", phone="0700000202", address="Kandahar")
        session.add_all([supplier_a, supplier_b, customer_a, customer_b])
        session.flush()

        # Raw materials (upsert by unique name so script is resilient to migration-created defaults)
        def upsert_material(name, unit, stock, cost_afg_per_unit, supplier_id, low_alert):
            material = session.query(RawMaterial).filter(RawMaterial.name == name).first()
            if material is None:
                material = RawMaterial(name=name)
                session.add(material)
            material.unit = unit
            material.current_stock = stock
            material.total_quantity_purchased = stock
            material.total_cost_purchased_afg = stock * cost_afg_per_unit
            material.total_cost_purchased_usd = (stock * cost_afg_per_unit) / ex_rate
            material.supplier_id = supplier_id
            material.low_stock_alert = low_alert
            return material

        corn = upsert_material("Corn", "kg", 1200, 24, supplier_a.id, 200)
        soybean = upsert_material("Soybean Meal", "kg", 900, 48, supplier_b.id, 150)
        carton = upsert_material("Carton", "pcs", 1500, 8, supplier_a.id, 200)
        tray = upsert_material("Tray", "pcs", 2200, 4, supplier_b.id, 300)
        session.flush()

        # Egg inventory baseline (upsert by unique grade)
        def upsert_inventory(grade, qty):
            row = session.query(EggInventory).filter(EggInventory.grade == grade).first()
            if row is None:
                row = EggInventory(grade=grade, current_stock=qty)
                session.add(row)
            else:
                row.current_stock = qty

        upsert_inventory(EggGrade.SMALL, 600)
        upsert_inventory(EggGrade.MEDIUM, 900)
        upsert_inventory(EggGrade.LARGE, 1200)
        upsert_inventory(EggGrade.BROKEN, 80)

        # Production history for last 10 days across sheds
        productions = []
        for day in range(10, 0, -1):
            d = now - timedelta(days=day)
            for idx, shed in enumerate(sheds):
                base = 260 + (idx * 15)
                productions.append(
                    EggProduction(
                        shed_id=shed.id,
                        date=d,
                        small_count=base // 4,
                        medium_count=base // 3,
                        large_count=base // 3,
                        broken_count=base // 12,
                        cartons_used=8 + idx,
                        trays_used=10 + idx,
                        notes="Seeded production",
                    )
                )
        session.add_all(productions)
        session.flush()

        # Purchases per farm + matching payments (for farm-aware cash flow)
        p1 = Purchase(
            party_id=supplier_a.id,
            farm_id=farm_a.id,
            material_id=corn.id,
            date=now - timedelta(days=6),
            quantity=300,
            rate_afg=24,
            rate_usd=24 / ex_rate,
            total_afg=7200,
            total_usd=7200 / ex_rate,
            exchange_rate_used=ex_rate,
            payment_method="Cash",
            notes="North corn purchase",
        )
        p2 = Purchase(
            party_id=supplier_b.id,
            farm_id=farm_b.id,
            material_id=soybean.id,
            date=now - timedelta(days=5),
            quantity=250,
            rate_afg=48,
            rate_usd=48 / ex_rate,
            total_afg=12000,
            total_usd=12000 / ex_rate,
            exchange_rate_used=ex_rate,
            payment_method="Cash",
            notes="South soybean purchase",
        )
        session.add_all([p1, p2])
        session.flush()

        session.add_all(
            [
                Payment(
                    party_id=supplier_a.id,
                    date=p1.date,
                    amount_afg=p1.total_afg,
                    amount_usd=p1.total_usd,
                    payment_type="Paid",
                    payment_method="Cash",
                    reference=f"Purchase #{p1.id}",
                    exchange_rate_used=ex_rate,
                    notes="Seed purchase payment",
                ),
                Payment(
                    party_id=supplier_b.id,
                    date=p2.date,
                    amount_afg=p2.total_afg,
                    amount_usd=p2.total_usd,
                    payment_type="Paid",
                    payment_method="Cash",
                    reference=f"Purchase #{p2.id}",
                    exchange_rate_used=ex_rate,
                    notes="Seed purchase payment",
                ),
            ]
        )

        # Sales per farm + matching payments
        s1 = Sale(
            party_id=customer_a.id,
            farm_id=farm_a.id,
            date=now - timedelta(days=3),
            quantity=420,
            rate_afg=6.0,
            rate_usd=6.0 / ex_rate,
            total_afg=2520,
            total_usd=2520 / ex_rate,
            exchange_rate_used=ex_rate,
            payment_method="Cash",
            notes="North farm sale",
        )
        s2 = Sale(
            party_id=customer_b.id,
            farm_id=farm_b.id,
            date=now - timedelta(days=2),
            quantity=390,
            rate_afg=6.2,
            rate_usd=6.2 / ex_rate,
            total_afg=2418,
            total_usd=2418 / ex_rate,
            exchange_rate_used=ex_rate,
            payment_method="Cash",
            notes="South farm sale",
        )
        session.add_all([s1, s2])
        session.flush()

        session.add_all(
            [
                Payment(
                    party_id=customer_a.id,
                    date=s1.date,
                    amount_afg=s1.total_afg,
                    amount_usd=s1.total_usd,
                    payment_type="Received",
                    payment_method="Cash",
                    reference=f"Sale #{s1.id}",
                    exchange_rate_used=ex_rate,
                    notes="Seed sale receipt",
                ),
                Payment(
                    party_id=customer_b.id,
                    date=s2.date,
                    amount_afg=s2.total_afg,
                    amount_usd=s2.total_usd,
                    payment_type="Received",
                    payment_method="Cash",
                    reference=f"Sale #{s2.id}",
                    exchange_rate_used=ex_rate,
                    notes="Seed sale receipt",
                ),
            ]
        )

        # Direct farm expenses
        session.add_all(
            [
                Expense(
                    farm_id=farm_a.id,
                    party_id=None,
                    date=now - timedelta(days=4),
                    category="Labor",
                    description="North labor",
                    amount_afg=1800,
                    amount_usd=1800 / ex_rate,
                    exchange_rate_used=ex_rate,
                    payment_method="Cash",
                ),
                Expense(
                    farm_id=farm_b.id,
                    party_id=None,
                    date=now - timedelta(days=4),
                    category="Electricity",
                    description="South electricity",
                    amount_afg=2100,
                    amount_usd=2100 / ex_rate,
                    exchange_rate_used=ex_rate,
                    payment_method="Cash",
                ),
            ]
        )

        session.commit()

        # Ensure admin account exists
        admin = UserManager.get_user_by_username("admin")
        if not admin:
            UserManager.create_user("admin", "Admin@123", "Administrator", "admin")

        return {
            "farms": 2,
            "sheds": len(sheds),
            "parties": 4,
            "materials": 4,
            "sales": 2,
            "purchases": 2,
            "payments": 4,
            "expenses": 2,
            "production_rows": len(productions),
        }
    finally:
        session.close()


def main() -> None:
    backup = reset_database_file()
    summary = seed_data()

    print("Database reset complete.")
    if backup:
        print(f"Backup created: {backup}")
    else:
        print("No previous database file found; created a new one.")

    print("Seed summary:")
    for key, value in summary.items():
        print(f"  - {key}: {value}")


if __name__ == "__main__":
    main()
