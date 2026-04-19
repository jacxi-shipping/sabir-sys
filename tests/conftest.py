"""Shared pytest fixtures for isolated database testing."""

import pytest
from PySide6.QtWidgets import QApplication
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from egg_farm_system.database.db import Base, DatabaseManager


@pytest.fixture(scope="session")
def qapp():
    """Provide a shared QApplication for Qt widget tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


@pytest.fixture
def isolated_db():
    """Provide an isolated in-memory database and patch DatabaseManager."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
        expire_on_commit=False,
    )
    Base.metadata.create_all(bind=engine)

    prev_engine = DatabaseManager._engine
    prev_session_local = DatabaseManager._SessionLocal
    DatabaseManager._engine = engine
    DatabaseManager._SessionLocal = SessionLocal

    try:
        yield SessionLocal
    finally:
        DatabaseManager._engine = prev_engine
        DatabaseManager._SessionLocal = prev_session_local
        engine.dispose()
