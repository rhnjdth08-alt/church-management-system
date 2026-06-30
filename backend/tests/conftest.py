"""Shared pytest fixtures.

The application creates its tables inside the FastAPI ``lifespan`` startup,
which only runs when ``TestClient`` is used as a context manager. The test
modules instantiate ``TestClient(app)`` at import time without a ``with``
block, so this fixture guarantees the schema exists (and is reset) for every
test, using an isolated on-disk SQLite database per test session.
"""

import pytest
from sqlmodel import SQLModel

from app.database import engine
from app.main import seed_default_divisions


@pytest.fixture(autouse=True)
def fresh_database():
    """Create all tables before each test and drop them afterwards.

    Running per-test keeps tests independent: seeded lookup data and members
    from one test never leak into another. Default divisions are seeded to
    mirror the application's startup behaviour (which the bare ``TestClient``
    used in these modules does not trigger).
    """
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    seed_default_divisions()
    yield
    SQLModel.metadata.drop_all(engine)
