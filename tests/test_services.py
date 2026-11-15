import os

import pytest


@pytest.mark.services
def test_postgres_migrations_and_sql(monkeypatch):
    if not os.environ.get("SERVICE_DATABASE_URL"):
        pytest.skip("Set SERVICE_DATABASE_URL to an isolated PostgreSQL test database")
    from alembic import command
    from alembic.config import Config
    from sqlalchemy import text

    from commerce.config import settings
    from commerce.db import engine

    monkeypatch.setenv("DATABASE_URL", os.environ["SERVICE_DATABASE_URL"])
    settings.cache_clear()
    engine.cache_clear()
    command.upgrade(Config("alembic.ini"), "head")
    with engine().connect() as connection:
        assert connection.execute(text("select version()")).scalar().startswith("PostgreSQL")
    from pathlib import Path

    from commerce.ingest import run_pipeline

    report = run_pipeline(Path("data/fixtures/retail.csv"), fixture=True)
    assert report["reconciled"] == 1
    with engine().connect() as connection:
        for path in Path("sql").rglob("*.sql"):
            connection.execute(text(path.read_text())).all()
    engine().dispose()
    engine.cache_clear()
    settings.cache_clear()


@pytest.mark.services
def test_real_broker_roundtrip_and_dlq(monkeypatch):
    if not os.environ.get("SERVICE_DATABASE_URL") or not os.environ.get("SERVICE_KAFKA_BOOTSTRAP_SERVERS"):
        pytest.skip("Requires isolated PostgreSQL and actual Kafka-compatible broker")
    import hashlib
    import uuid
    from datetime import UTC, datetime

    from sqlalchemy import select

    from commerce.config import settings
    from commerce.db import engine, events, initialize
    from commerce.streaming import TransactionEvent, consume, ensure_topics, producer, publish

    monkeypatch.setenv("DATABASE_URL", os.environ["SERVICE_DATABASE_URL"])
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", os.environ["SERVICE_KAFKA_BOOTSTRAP_SERVERS"])
    identity = uuid.uuid4().hex
    monkeypatch.setenv("KAFKA_TOPIC", "test.retail." + identity)
    monkeypatch.setenv("KAFKA_GROUP", "test.consumer." + identity)
    settings.cache_clear()
    engine.cache_clear()
    initialize()
    ensure_topics()
    event = TransactionEvent(
        event_id=hashlib.sha256(identity.encode()).hexdigest(),
        source="historical_replay",
        invoice="test123",
        stock_code="12345",
        quantity=1,
        unit_price="2.55",
        event_time=datetime(2011, 1, 1, tzinfo=UTC),
        replay_time=datetime.now(UTC),
    )
    publish(event)
    client = producer()
    client.produce(settings().kafka_topic, value=b'{"invalid":true}')
    assert client.flush(20) == 0
    consume(limit=2)
    with engine().connect() as connection:
        assert (
            connection.scalar(select(events.c.status).where(events.c.event_id == event.event_id))
            == "processed"
        )
        assert connection.scalar(
            select(events.c.event_id).where(
                events.c.topic == settings().kafka_topic, events.c.status == "rejected"
            )
        )
    engine().dispose()
    engine.cache_clear()
    settings.cache_clear()
