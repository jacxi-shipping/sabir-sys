"""Pytest-style validation tests for import data validators."""

from egg_farm_system.utils.data_validator import DataValidator


def test_expense_validation_requires_farm_name():
    data_missing_farm = [
        {
            "date": "2026-01-15",
            "category": "Labor",
            "amount_afg": 5000,
            "amount_usd": 64,
            "payment_method": "Cash",
        }
    ]
    valid, errors = DataValidator.validate_expenses(data_missing_farm)
    assert valid == []
    assert errors
    assert "Farm name is required" in errors[0]


def test_expense_validation_valid_payload():
    data_valid = [
        {
            "date": "2026-01-15",
            "farm_name": "Test Farm",
            "category": "Labor",
            "amount_afg": 5000,
            "amount_usd": 64,
            "payment_method": "Cash",
        }
    ]
    valid, errors = DataValidator.validate_expenses(data_valid)
    assert len(valid) == 1
    assert errors == []


def test_expense_validation_defaults_usd_to_zero():
    data_no_usd = [
        {
            "date": "2026-01-15",
            "farm_name": "Test Farm",
            "category": "Labor",
            "amount_afg": 5000,
            "payment_method": "Cash",
        }
    ]
    valid, errors = DataValidator.validate_expenses(data_no_usd)
    assert len(valid) == 1
    assert errors == []
    assert valid[0]["amount_usd"] == 0


def test_expense_validation_rejects_invalid_category():
    data_invalid_category = [
        {
            "date": "2026-01-15",
            "farm_name": "Test Farm",
            "category": "InvalidCategory",
            "amount_afg": 5000,
            "payment_method": "Cash",
        }
    ]
    valid, errors = DataValidator.validate_expenses(data_invalid_category)
    assert valid == []
    assert errors
    assert "Invalid category" in errors[0]


def test_party_raw_material_employee_validation_still_works():
    valid, errors = DataValidator.validate_parties([{"name": "Test Party", "phone": "+93701234567"}])
    assert len(valid) == 1
    assert errors == []

    valid, errors = DataValidator.validate_raw_materials([{"name": "Test Material", "unit": "kg", "low_stock_alert": 100}])
    assert len(valid) == 1
    assert errors == []

    valid, errors = DataValidator.validate_employees([
        {
            "full_name": "Test Employee",
            "job_title": "Worker",
            "salary_amount": 10000,
            "salary_period": "Monthly",
        }
    ])
    assert len(valid) == 1
    assert errors == []
