"""Pytest-style import flow tests for expense import fixes."""

import csv
from pathlib import Path

import pytest

from egg_farm_system.database.models import Expense, Farm
from egg_farm_system.utils.data_importer import DataImporter


def test_expense_import_calculates_exchange_rate(isolated_db, tmp_path: Path):
    session = isolated_db()

    farm = Farm(name="Test Farm Import", location="Test Location")
    session.add(farm)
    session.commit()

    csv_path = tmp_path / "expenses.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "farm_name", "category", "amount_afg", "amount_usd", "description", "payment_method"])
        writer.writerow(["2026-01-15", "Test Farm Import", "Labor", "5000", "64", "Test expense", "Cash"])

    importer = DataImporter(session=session)
    result = importer.import_expenses(str(csv_path), user_id=1)

    assert result["status"] == "success"
    assert result["imported"] == 1
    assert not result["errors"]

    expense = session.query(Expense).filter(Expense.description == "Test expense").first()
    assert expense is not None
    assert expense.exchange_rate_used is not None
    assert expense.exchange_rate_used == pytest.approx(5000 / 64)


def test_expense_import_fails_when_farm_missing(isolated_db, tmp_path: Path):
    session = isolated_db()

    csv_path = tmp_path / "expenses_missing_farm.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["date", "farm_name", "category", "amount_afg", "amount_usd", "description", "payment_method"])
        writer.writerow(["2026-01-15", "Unknown Farm", "Labor", "5000", "64", "Missing farm case", "Cash"])

    importer = DataImporter(session=session)
    result = importer.import_expenses(str(csv_path), user_id=1)

    assert result["status"] == "failed"
    assert result["imported"] == 0
    assert result["errors"]
    assert "not found" in " ".join(result["errors"])
