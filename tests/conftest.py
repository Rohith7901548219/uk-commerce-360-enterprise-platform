from pathlib import Path

import pytest

from commerce.config import settings
from commerce.db import engine


@pytest.fixture
def warehouse(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'test.db'}")
    monkeypatch.setenv("CUSTOMER_HASH_KEY", "unit-test-secret-only")
    monkeypatch.setenv("WRITE_API_TOKEN", "unit-test-write-token")
    settings.cache_clear()
    engine.cache_clear()
    from commerce.ingest import run_pipeline

    run_pipeline(Path("data/fixtures/retail.csv"), fixture=True, chunk_size=2)
    yield
    engine().dispose()
    engine.cache_clear()
    settings.cache_clear()


@pytest.fixture
def client(warehouse):
    from fastapi.testclient import TestClient

    from commerce.api import app

    with TestClient(app) as instance:
        yield instance
