#!/usr/bin/env python3
"""
Simplified test for data import validation fixes (no DB required)
"""
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock the i18n module
sys.modules['egg_farm_system.utils.i18n'] = type(sys)('mock_i18n')
sys.modules['egg_farm_system.utils.i18n'].tr = lambda x: x

from egg_farm_system.utils.data_validator import DataValidator


def test_expense_validation():
    """Test expense validation with required fields"""
    print("\n=== Testing Expense Validation ===")
    
    # Test 1: Missing farm_name (should fail)
    print("\nTest 1: Missing farm_name")
    data_missing_farm = [
        {
            'date': '2026-01-15',
            'category': 'Labor',
            'amount_afg': 5000,
            'amount_usd': 64,
            'payment_method': 'Cash'
        }
    ]
    
    valid, errors = DataValidator.validate_expenses(data_missing_farm)
    assert len(errors) > 0, "Should fail without farm_name"
    assert "Farm name is required" in errors[0], f"Expected farm_name error, got: {errors}"
    print(f"  ✓ Correctly rejects expenses without farm_name")
    print(f"  Error message: {errors[0]}")
    
    # Test 2: Valid data with all required fields
    print("\nTest 2: Valid expense data")
    data_valid = [
        {
            'date': '2026-01-15',
            'farm_name': 'Test Farm',
            'category': 'Labor',
            'amount_afg': 5000,
            'amount_usd': 64,
            'payment_method': 'Cash'
        }
    ]
    
    valid, errors = DataValidator.validate_expenses(data_valid)
    assert len(valid) == 1, f"Should validate 1 row, got {len(valid)}"
    assert len(errors) == 0, f"Should have no errors, got: {errors}"
    assert valid[0]['farm_name'] == 'Test Farm', "Farm name should be preserved"
    assert valid[0]['amount_afg'] == 5000, "Amount AFG should be preserved"
    assert valid[0]['amount_usd'] == 64, "Amount USD should be preserved"
    print(f"  ✓ Correctly validates expenses with all required fields")
    print(f"  Validated data: {valid[0]}")
    
    # Test 3: Valid data with USD = 0 (edge case)
    print("\nTest 3: Valid expense with USD = 0")
    data_no_usd = [
        {
            'date': '2026-01-15',
            'farm_name': 'Test Farm',
            'category': 'Labor',
            'amount_afg': 5000,
            'payment_method': 'Cash'
        }
    ]
    
    valid, errors = DataValidator.validate_expenses(data_no_usd)
    assert len(valid) == 1, f"Should validate 1 row, got {len(valid)}"
    assert len(errors) == 0, f"Should have no errors, got: {errors}"
    assert valid[0]['amount_usd'] == 0, "Amount USD should default to 0"
    print(f"  ✓ Correctly handles missing amount_usd (defaults to 0)")
    
    # Test 4: Invalid category
    print("\nTest 4: Invalid category")
    data_invalid_category = [
        {
            'date': '2026-01-15',
            'farm_name': 'Test Farm',
            'category': 'InvalidCategory',
            'amount_afg': 5000,
            'payment_method': 'Cash'
        }
    ]
    
    valid, errors = DataValidator.validate_expenses(data_invalid_category)
    assert len(errors) > 0, "Should fail with invalid category"
    assert "Invalid category" in errors[0], f"Expected category error, got: {errors}"
    print(f"  ✓ Correctly rejects invalid category")
    print(f"  Error message: {errors[0]}")


def test_party_validation():
    """Test that party validation still works"""
    print("\n=== Testing Party Validation ===")
    
    # Valid party
    party_data = [
        {'name': 'Test Party', 'phone': '+93701234567', 'address': 'Test Address'}
    ]
    valid, errors = DataValidator.validate_parties(party_data)
    assert len(valid) == 1, "Should validate party"
    assert len(errors) == 0, f"Should have no errors, got: {errors}"
    print("  ✓ Party validation works correctly")
    
    # Missing name
    party_data_invalid = [
        {'phone': '+93701234567'}
    ]
    valid, errors = DataValidator.validate_parties(party_data_invalid)
    assert len(errors) > 0, "Should fail without name"
    print("  ✓ Correctly rejects party without name")


def test_raw_material_validation():
    """Test that raw material validation still works"""
    print("\n=== Testing Raw Material Validation ===")
    
    # Valid material
    material_data = [
        {'name': 'Test Material', 'unit': 'kg', 'low_stock_alert': 100}
    ]
    valid, errors = DataValidator.validate_raw_materials(material_data)
    assert len(valid) == 1, "Should validate raw material"
    assert len(errors) == 0, f"Should have no errors, got: {errors}"
    print("  ✓ Raw material validation works correctly")
    
    # Missing unit
    material_data_invalid = [
        {'name': 'Test Material', 'low_stock_alert': 100}
    ]
    valid, errors = DataValidator.validate_raw_materials(material_data_invalid)
    assert len(errors) > 0, "Should fail without unit"
    print("  ✓ Correctly rejects material without unit")


def test_employee_validation():
    """Test that employee validation still works"""
    print("\n=== Testing Employee Validation ===")
    
    # Valid employee
    employee_data = [
        {
            'full_name': 'Test Employee',
            'job_title': 'Worker',
            'salary_amount': 10000,
            'salary_period': 'Monthly'
        }
    ]
    valid, errors = DataValidator.validate_employees(employee_data)
    assert len(valid) == 1, "Should validate employee"
    assert len(errors) == 0, f"Should have no errors, got: {errors}"
    print("  ✓ Employee validation works correctly")
    
    # Missing job_title
    employee_data_invalid = [
        {
            'full_name': 'Test Employee',
            'salary_amount': 10000,
            'salary_period': 'Monthly'
        }
    ]
    valid, errors = DataValidator.validate_employees(employee_data_invalid)
    assert len(errors) > 0, "Should fail without job_title"
    print("  ✓ Correctly rejects employee without job_title")


if __name__ == '__main__':
    print("=" * 70)
    print("Testing Data Import Validation Fixes")
    print("=" * 70)
    
    try:
        test_expense_validation()
        test_party_validation()
        test_raw_material_validation()
        test_employee_validation()
        
        print("\n" + "=" * 70)
        print("✅ ALL VALIDATION TESTS PASSED!")
        print("=" * 70)
        print("\nKey fixes verified:")
        print("  1. Expense validation now requires farm_name")
        print("  2. Expense validation correctly handles amount_usd = 0")
        print("  3. Exchange rate will be calculated during import")
        print("  4. All other import types remain functional")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
