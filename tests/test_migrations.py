from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from commerce.config import settings
from commerce.db import engine


def test_alembic_upgrade_is_repeatable(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'migration.db'}")
    settings.cache_clear()
    engine.cache_clear()
    command.upgrade(Config("alembic.ini"), "head")
    command.upgrade(Config("alembic.ini"), "head")
    assert "fact_sales_transactions" in inspect(engine()).get_table_names()
    with engine().connect() as connection:
        assert connection.execute(text("select version_num from alembic_version")).scalar() == "0001"
    engine().dispose()
    engine.cache_clear()
    settings.cache_clear()
