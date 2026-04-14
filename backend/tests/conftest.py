import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models import Base


@pytest.fixture
def memory_session_factory(monkeypatch):
    """In-memory SQLite + patch readings_store SessionLocal."""
    eng = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(eng)
    Sess = sessionmaker(bind=eng)
    monkeypatch.setattr("app.readings_store.SessionLocal", Sess)
    return Sess
