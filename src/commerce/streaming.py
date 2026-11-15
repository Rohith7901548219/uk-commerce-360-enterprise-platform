"""Real Kafka publishing and durable at-least-once consumption; no simulated counters."""

import hashlib
import json
import logging
import time
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Literal

from confluent_kafka import Consumer, KafkaException, Producer
from confluent_kafka.admin import AdminClient, NewTopic
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from sqlalchemy import and_, func, or_, select

from commerce.config import settings
from commerce.db import engine, events, insert_ignore, sales, stream_state

LOGGER = logging.getLogger(__name__)


class TransactionEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(pattern=r"^[a-f0-9]{64}$")
    source: Literal["historical_replay", "authorized_webhook"]
    invoice: str = Field(min_length=1, max_length=40)
    stock_code: str = Field(min_length=1, max_length=30)
    customer_key: str | None = Field(default=None, pattern=r"^[a-f0-9]{24}$")
    quantity: int = Field(ge=-2147483647, le=2147483647)
    unit_price: Decimal = Field(gt=0, max_digits=18, decimal_places=4)
    event_time: datetime
    replay_time: datetime | None = None

    @field_validator("quantity")
    @classmethod
    def nonzero_quantity(cls, value):
        if value == 0:
            raise ValueError("Transaction quantity must be nonzero")
        return value

    @model_validator(mode="after")
    def source_times(self):
        if self.source == "historical_replay" and self.replay_time is None:
            raise ValueError("Historical replay requires replay_time")
        if self.source == "authorized_webhook" and self.replay_time is not None:
            raise ValueError("External webhook events cannot have replay_time")
        return self

    @field_validator("event_time", "replay_time")
    @classmethod
    def require_zone(cls, value):
        if value is not None and value.tzinfo is None:
            raise ValueError("Explicit timestamp timezone is required")
        return value


def state(key, default=None):
    with engine().connect() as connection:
        value = connection.scalar(select(stream_state.c.value).where(stream_state.c.key == key))
    return default if value is None else value


def set_state(key, value):
    with engine().begin() as connection:
        if connection.dialect.name == "postgresql":
            from sqlalchemy.dialects.postgresql import insert
        else:
            from sqlalchemy.dialects.sqlite import insert
        statement = insert(stream_state).values(key=key, value=value, updated_at=datetime.now(UTC))
        connection.execute(
            statement.on_conflict_do_update(
                index_elements=[stream_state.c.key], set_={"value": value, "updated_at": datetime.now(UTC)}
            )
        )


def producer():
    return Producer(
        {
            "bootstrap.servers": settings().kafka_bootstrap_servers,
            "enable.idempotence": True,
            "acks": "all",
            "delivery.timeout.ms": 15000,
            "socket.timeout.ms": 5000,
        }
    )


def ensure_topics():
    admin = AdminClient({"bootstrap.servers": settings().kafka_bootstrap_servers, "socket.timeout.ms": 5000})
    existing = admin.list_topics(timeout=5).topics
    missing = [
        NewTopic(name, num_partitions=1, replication_factor=1)
        for name in (settings().kafka_topic, settings().kafka_topic + ".dlq")
        if name not in existing
    ]
    for future in admin.create_topics(missing).values():
        future.result(timeout=10)


def publish(value: TransactionEvent, client=None):
    client = client or producer()
    failures = []
    client.produce(
        settings().kafka_topic,
        key=value.event_id,
        value=value.model_dump_json(),
        on_delivery=lambda error, message: failures.append(str(error)) if error else None,
    )
    if client.flush(20) or failures:
        raise RuntimeError(f"Broker did not acknowledge event: {failures}")


def produce_replay(limit=0):
    ensure_topics()
    client = producer()
    sent = 0
    set_state("producer", {"status": "running", "heartbeat": datetime.now(UTC).isoformat()})
    try:
        while not limit or sent < limit:
            control = state("control", {"action": "start", "speed": 10})
            action = control.get("action", "start")
            set_state("producer", {"status": action, "heartbeat": datetime.now(UTC).isoformat()})
            if action in ("stop", "pause"):
                if limit:
                    return
                time.sleep(0.5)
                continue
            if action == "reset":
                set_state("cursor", None)
                set_state("control", {"action": "pause", "speed": control.get("speed", 10)})
                continue
            cursor = state("cursor")
            with engine().connect() as connection:
                query = select(sales)
                if isinstance(cursor, dict):
                    previous_time = datetime.fromisoformat(cursor["event_time"])
                    query = query.where(
                        or_(
                            sales.c.event_time > previous_time,
                            and_(
                                sales.c.event_time == previous_time,
                                sales.c.transaction_id > cursor["transaction_id"],
                            ),
                        )
                    )
                batch = (
                    connection.execute(
                        query.order_by(sales.c.event_time, sales.c.transaction_id).limit(
                            min(100, limit - sent) if limit else 100
                        )
                    )
                    .mappings()
                    .all()
                )
            if not batch:
                set_state("producer", {"status": "complete", "heartbeat": datetime.now(UTC).isoformat()})
                if limit:
                    return
                set_state("control", {"action": "pause", "speed": control.get("speed", 10)})
                continue
            for row in batch:
                # Refresh the control between events so pause and stop take effect promptly.
                if state("control", {"action": "start"}).get("action") != "start":
                    break
                event_time = row["event_time"]
                if event_time.tzinfo is None:
                    event_time = event_time.replace(tzinfo=UTC)
                value = TransactionEvent(
                    event_id=hashlib.sha256(f"replay:{row['transaction_id']}".encode()).hexdigest(),
                    source="historical_replay",
                    invoice=row["invoice"],
                    stock_code=row["stock_code"],
                    customer_key=row["customer_key"],
                    quantity=row["quantity"],
                    unit_price=row["unit_price"],
                    event_time=event_time,
                    replay_time=datetime.now(UTC),
                )
                publish(value, client)
                set_state(
                    "cursor", {"event_time": event_time.isoformat(), "transaction_id": row["transaction_id"]}
                )
                sent += 1
                time.sleep(1 / max(0.1, float(control.get("speed", 10))))
                if limit and sent >= limit:
                    break
    except Exception as error:
        set_state(
            "producer",
            {"status": "error", "error": str(error)[:500], "heartbeat": datetime.now(UTC).isoformat()},
        )
        raise


def process_event(payload: bytes, topic="direct-test", partition=0, offset=0):
    value = TransactionEvent.model_validate_json(payload)
    with engine().begin() as connection:
        existing = connection.execute(
            select(events.c.payload).where(events.c.event_id == value.event_id)
        ).scalar()
        if existing:
            comparison = value.model_dump(mode="json")
            if {k: v for k, v in existing.items() if k != "replay_time"} != {
                k: v for k, v in comparison.items() if k != "replay_time"
            }:
                raise ValueError("Event ID conflicts with a previously committed transaction")
        insert_ignore(
            connection,
            events,
            [
                {
                    "event_id": value.event_id,
                    "source": value.source,
                    "event_time": value.event_time,
                    "replay_time": value.replay_time,
                    "ingestion_time": datetime.now(UTC),
                    "status": "processed",
                    "topic": topic,
                    "partition_id": partition,
                    "offset_id": offset,
                    "payload": value.model_dump(mode="json"),
                }
            ],
        )
    return "duplicate" if existing else "processed"


def consumer_snapshot(client, status, last_result=None):
    assignments = client.assignment()
    lag = 0
    for assignment in assignments:
        _, high = client.get_watermark_offsets(assignment, timeout=2)
        position = client.position([assignment])[0].offset
        lag += max(0, high - max(position, 0))
    now = datetime.now(UTC).isoformat()
    set_state(
        "consumer",
        {
            "status": status,
            "last_result": last_result,
            "lag": lag if assignments else None,
            "heartbeat": now,
            "broker_observed_at": now if assignments else None,
        },
    )


def consume(limit=0):
    ensure_topics()
    client = Consumer(
        {
            "bootstrap.servers": settings().kafka_bootstrap_servers,
            "group.id": settings().kafka_group,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
    )
    dead_letter = producer()
    client.subscribe([settings().kafka_topic])
    processed = 0
    last_message_at = time.monotonic()
    try:
        while not limit or processed < limit:
            message = client.poll(1)
            if message is None:
                consumer_snapshot(client, "polling")
                if limit and time.monotonic() - last_message_at > 60:
                    raise TimeoutError("Timed out waiting for the requested broker test messages")
                continue
            if message.error():
                raise KafkaException(message.error())
            payload = message.value()
            try:
                result = process_event(payload, message.topic(), message.partition(), message.offset())
            except ValueError as error:
                # Acknowledge the DLQ publish before committing the failed source offset.
                failures = []
                body = {
                    "payload": payload.decode(errors="replace"),
                    "error": str(error),
                    "source_topic": message.topic(),
                    "source_offset": message.offset(),
                }
                dead_letter.produce(
                    settings().kafka_topic + ".dlq",
                    value=json.dumps(body),
                    on_delivery=lambda err, msg: failures.append(str(err)) if err else None,
                )
                if dead_letter.flush(20) or failures:
                    raise RuntimeError("DLQ delivery failed; source offset was not committed") from error
                with engine().begin() as connection:
                    rejected_id = hashlib.sha256(
                        f"reject:{message.topic()}:{message.partition()}:{message.offset()}".encode()
                    ).hexdigest()
                    insert_ignore(
                        connection,
                        events,
                        [
                            {
                                "event_id": rejected_id,
                                "source": "invalid",
                                "ingestion_time": datetime.now(UTC),
                                "status": "rejected",
                                "topic": message.topic(),
                                "partition_id": message.partition(),
                                "offset_id": message.offset(),
                                "payload": body,
                            }
                        ],
                    )
                result = "rejected"
            # Database failures propagate without committing; supervisor restarts and retries.
            client.commit(message=message, asynchronous=False)
            processed += 1
            last_message_at = time.monotonic()
            consumer_snapshot(client, "running", result)
    except Exception as error:
        set_state(
            "consumer",
            {"status": "error", "error": str(error)[:500], "heartbeat": datetime.now(UTC).isoformat()},
        )
        LOGGER.exception("Consumer failed; uncommitted messages will retry after restart")
        raise
    finally:
        client.close()


def stream_status():
    now = datetime.now(UTC)
    with engine().connect() as connection:
        counts = dict(
            connection.execute(select(events.c.status, func.count()).group_by(events.c.status)).all()
        )
        recent_count = connection.scalar(
            select(func.count())
            .select_from(events)
            .where(events.c.ingestion_time >= now - timedelta(seconds=60))
        )
        last = connection.scalar(select(func.max(events.c.ingestion_time)))
    consumer = state("consumer", {})
    heartbeat = consumer.get("heartbeat")
    broker_observed_at = consumer.get("broker_observed_at")
    healthy = bool(
        heartbeat
        and (now - datetime.fromisoformat(heartbeat)).total_seconds() < 15
        and broker_observed_at
        and (now - datetime.fromisoformat(broker_observed_at)).total_seconds() < 15
        and consumer.get("status") != "error"
    )
    return {
        "label": "HISTORICAL TRANSACTION REPLAY — DEMONSTRATION",
        "counts": counts,
        "events_ingested": sum(counts.values()),
        "processed": counts.get("processed", 0),
        "rejected": counts.get("rejected", 0),
        "throughput_per_second_last_minute": recent_count / 60,
        "last_ingestion_time": last,
        "consumer": consumer,
        "producer": state("producer", {}),
        "control": state("control", {}),
        "healthy": healthy,
        "consumer_lag": consumer.get("lag") if healthy else None,
    }
