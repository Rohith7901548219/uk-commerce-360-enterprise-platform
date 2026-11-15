import hashlib
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from commerce.streaming import TransactionEvent, process_event, set_state, stream_status


def body():
    return dict(
        event_id=hashlib.sha256(b"validation-test").hexdigest(),
        source="authorized_webhook",
        invoice="1",
        stock_code="12345",
        quantity=1,
        unit_price="2.0000",
        event_time=datetime.now(UTC),
    )


def test_zero_quantity_and_source_timestamp_contract():
    value = body()
    value["quantity"] = 0
    with pytest.raises(ValidationError):
        TransactionEvent(**value)
    value = body()
    value["source"] = "historical_replay"
    with pytest.raises(ValidationError):
        TransactionEvent(**value)


def test_conflicting_event_id_is_rejected(warehouse):
    value = TransactionEvent(**body())
    process_event(value.model_dump_json().encode(), offset=50)
    changed = value.model_copy(update={"quantity": 2})
    with pytest.raises(ValueError, match="conflicts"):
        process_event(changed.model_dump_json().encode(), offset=51)


def test_fresh_worker_without_observed_broker_is_not_healthy(warehouse):
    set_state("consumer", {"status": "polling", "heartbeat": datetime.now(UTC).isoformat(), "lag": 0})
    status = stream_status()
    assert status["healthy"] is False
    assert status["consumer_lag"] is None
