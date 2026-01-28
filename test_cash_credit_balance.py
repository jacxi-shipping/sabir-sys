"""
Test to verify Cash transaction balance behavior

This test verifies that:
1. Cash sales result in zero party balance
2. Credit sales result in positive party balance
3. Cash purchases result in zero party balance
4. Credit purchases result in negative party balance
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from datetime import datetime
from egg_farm_system.database.db import DatabaseManager
from egg_farm_system.modules.sales import SalesManager
from egg_farm_system.modules.purchases import PurchaseManager
from egg_farm_system.modules.ledger import LedgerManager
from egg_farm_system.modules.parties import PartyManager
from egg_farm_system.database.models import RawMaterial


def test_cash_sale_balance():
    """Test that Cash sales result in zero balance"""
    print("\n=== Testing Cash Sale Balance ===")
    
    # Create a test party
    party_manager = PartyManager()
    party = party_manager.create_party(
        name=f"Test Party Cash Sale {datetime.now().timestamp()}",
        phone="1234567890",
        address="Test Address"
    )
    party_id = party.id
    print(f"Created test party: {party.name} (ID: {party_id})")
    
    # Record a Cash sale
    with SalesManager() as sales_manager:
        sale = sales_manager.record_sale(
            party_id=party_id,
            quantity=100,
            rate_afg=50.0,
            rate_usd=0.64,
            payment_method="Cash"
        )
        print(f"Recorded Cash sale: {sale.quantity} eggs for {sale.total_afg} AFG")
    
    # Check balance
    ledger_manager = LedgerManager()
    balance_afg = ledger_manager.get_party_balance(party_id, "AFG")
    balance_usd = ledger_manager.get_party_balance(party_id, "USD")
    
    print(f"Party balance AFG: {balance_afg}")
    print(f"Party balance USD: {balance_usd}")
    
    # Verify balance is zero
    if abs(balance_afg) < 0.01 and abs(balance_usd) < 0.01:
        print("✅ PASS: Cash sale results in zero balance")
        return True
    else:
        print(f"❌ FAIL: Cash sale balance should be 0, got AFG={balance_afg}, USD={balance_usd}")
        return False


def test_credit_sale_balance():
    """Test that Credit sales result in positive balance"""
    print("\n=== Testing Credit Sale Balance ===")
    
    # Create a test party
    party_manager = PartyManager()
    party = party_manager.create_party(
        name=f"Test Party Credit Sale {datetime.now().timestamp()}",
        phone="1234567890",
        address="Test Address"
    )
    party_id = party.id
    print(f"Created test party: {party.name} (ID: {party_id})")
    
    # Record a Credit sale
    with SalesManager() as sales_manager:
        sale = sales_manager.record_sale(
            party_id=party_id,
            quantity=200,
            rate_afg=50.0,
            rate_usd=0.64,
            payment_method="Credit"
        )
        print(f"Recorded Credit sale: {sale.quantity} eggs for {sale.total_afg} AFG")
    
    # Check balance
    ledger_manager = LedgerManager()
    balance_afg = ledger_manager.get_party_balance(party_id, "AFG")
    balance_usd = ledger_manager.get_party_balance(party_id, "USD")
    
    print(f"Party balance AFG: {balance_afg}")
    print(f"Party balance USD: {balance_usd}")
    
    # Verify balance is positive (they owe us)
    expected_afg = 200 * 50.0  # 10,000
    expected_usd = 200 * 0.64  # 128
    
    if abs(balance_afg - expected_afg) < 0.01 and abs(balance_usd - expected_usd) < 0.01:
        print(f"✅ PASS: Credit sale results in positive balance (receivable)")
        return True
    else:
        print(f"❌ FAIL: Credit sale balance should be {expected_afg} AFG, got {balance_afg}")
        return False


def test_cash_purchase_balance():
    """Test that Cash purchases result in zero balance"""
    print("\n=== Testing Cash Purchase Balance ===")
    
    # Create a test party
    party_manager = PartyManager()
    party = party_manager.create_party(
        name=f"Test Party Cash Purchase {datetime.now().timestamp()}",
        phone="1234567890",
        address="Test Address"
    )
    party_id = party.id
    print(f"Created test party: {party.name} (ID: {party_id})")
    
    # Ensure a material exists
    session = DatabaseManager.get_session()
    material = session.query(RawMaterial).filter(RawMaterial.name == "Test Material").first()
    if not material:
        material = RawMaterial(name="Test Material", unit="kg", current_stock=0)
        session.add(material)
        session.commit()
    material_id = material.id
    session.close()
    
    # Record a Cash purchase
    with PurchaseManager() as purchase_manager:
        purchase = purchase_manager.record_purchase(
            party_id=party_id,
            material_id=material_id,
            quantity=50,
            rate_afg=100.0,
            rate_usd=1.28,
            payment_method="Cash"
        )
        print(f"Recorded Cash purchase: {purchase.quantity}kg for {purchase.total_afg} AFG")
    
    # Check balance
    ledger_manager = LedgerManager()
    balance_afg = ledger_manager.get_party_balance(party_id, "AFG")
    balance_usd = ledger_manager.get_party_balance(party_id, "USD")
    
    print(f"Party balance AFG: {balance_afg}")
    print(f"Party balance USD: {balance_usd}")
    
    # Verify balance is zero
    if abs(balance_afg) < 0.01 and abs(balance_usd) < 0.01:
        print("✅ PASS: Cash purchase results in zero balance")
        return True
    else:
        print(f"❌ FAIL: Cash purchase balance should be 0, got AFG={balance_afg}, USD={balance_usd}")
        return False


def test_credit_purchase_balance():
    """Test that Credit purchases result in negative balance"""
    print("\n=== Testing Credit Purchase Balance ===")
    
    # Create a test party
    party_manager = PartyManager()
    party = party_manager.create_party(
        name=f"Test Party Credit Purchase {datetime.now().timestamp()}",
        phone="1234567890",
        address="Test Address"
    )
    party_id = party.id
    print(f"Created test party: {party.name} (ID: {party_id})")
    
    # Ensure a material exists
    session = DatabaseManager.get_session()
    material = session.query(RawMaterial).filter(RawMaterial.name == "Test Material").first()
    if not material:
        material = RawMaterial(name="Test Material", unit="kg", current_stock=0)
        session.add(material)
        session.commit()
    material_id = material.id
    session.close()
    
    # Record a Credit purchase
    with PurchaseManager() as purchase_manager:
        purchase = purchase_manager.record_purchase(
            party_id=party_id,
            material_id=material_id,
            quantity=75,
            rate_afg=100.0,
            rate_usd=1.28,
            payment_method="Credit"
        )
        print(f"Recorded Credit purchase: {purchase.quantity}kg for {purchase.total_afg} AFG")
    
    # Check balance
    ledger_manager = LedgerManager()
    balance_afg = ledger_manager.get_party_balance(party_id, "AFG")
    balance_usd = ledger_manager.get_party_balance(party_id, "USD")
    
    print(f"Party balance AFG: {balance_afg}")
    print(f"Party balance USD: {balance_usd}")
    
    # Verify balance is negative (we owe them)
    expected_afg = -(75 * 100.0)  # -7,500
    expected_usd = -(75 * 1.28)   # -96
    
    if abs(balance_afg - expected_afg) < 0.01 and abs(balance_usd - expected_usd) < 0.01:
        print(f"✅ PASS: Credit purchase results in negative balance (payable)")
        return True
    else:
        print(f"❌ FAIL: Credit purchase balance should be {expected_afg} AFG, got {balance_afg}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("Cash and Credit Payment Balance Tests")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(("Cash Sale", test_cash_sale_balance()))
    except Exception as e:
        print(f"❌ FAIL: Cash Sale test raised exception: {e}")
        results.append(("Cash Sale", False))
    
    try:
        results.append(("Credit Sale", test_credit_sale_balance()))
    except Exception as e:
        print(f"❌ FAIL: Credit Sale test raised exception: {e}")
        results.append(("Credit Sale", False))
    
    try:
        results.append(("Cash Purchase", test_cash_purchase_balance()))
    except Exception as e:
        print(f"❌ FAIL: Cash Purchase test raised exception: {e}")
        results.append(("Cash Purchase", False))
    
    try:
        results.append(("Credit Purchase", test_credit_purchase_balance()))
    except Exception as e:
        print(f"❌ FAIL: Credit Purchase test raised exception: {e}")
        results.append(("Credit Purchase", False))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nTotal: {passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️ {total_count - passed_count} test(s) failed")
        sys.exit(1)
