import hashlib
from datetime import UTC, datetime

import pandas as pd
import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from commerce.analytics import basket_rules, retention, rfm, sales_frame
from commerce.db import engine, events
from commerce.ml import FEATURES, features_at, predict_series
from commerce.streaming import TransactionEvent, process_event, stream_status


def test_feature_horizon_and_future_invariance(warehouse):
    frame = sales_frame()
    cutoff = "2010-02-01"
    first = features_at(frame, cutoff)
    future = frame.copy()
    future.loc[future.event_time >= pd.Timestamp(cutoff, tz="UTC"), "amount"] = 999999
    second = features_at(future, cutoff)
    pd.testing.assert_frame_equal(first[FEATURES], second[FEATURES])
    assert first.iloc[0].frequency == 1
    assert first.iloc[0].monetary == 18.5
    assert first.iloc[0].target == 0
    assert (first.feature_max_time < first.cutoff).all()


def test_segmentation_and_cohorts(warehouse):
    frame = sales_frame()
    assert len(rfm(frame)) == 2
    cohorts = retention(frame)
    assert cohorts.retention_rate.between(0, 1).all()
    assert (cohorts[cohorts.period == 0].retention_rate == 1).all()
    rules = basket_rules(frame, min_support=0.01)
    assert rules
    assert all(x["support"] <= 1 and x["confidence"] <= 1 and x["lift"] > 0 for x in rules)


def test_forecast_baselines_are_causal():
    assert predict_series(range(1, 101), 3, "naive").tolist() == [100, 100, 100]
    assert predict_series(range(1, 101), 8, "seasonal_naive").tolist() == [94, 95, 96, 97, 98, 99, 100, 94]
    assert len(predict_series(range(1, 101), 8, "ridge_autoregression")) == 8


def event():
    return TransactionEvent(
        event_id=hashlib.sha256(b"event-test").hexdigest(),
        source="historical_replay",
        invoice="123",
        stock_code="12345",
        quantity=1,
        unit_price="2.55",
        event_time=datetime(2011, 1, 1, tzinfo=UTC),
        replay_time=datetime.now(UTC),
    )


def test_idempotent_event_processing_does_not_change_sales(warehouse):
    from commerce.analytics import kpis

    before = kpis()["net_sales"]
    value = event()
    assert process_event(value.model_dump_json().encode(), offset=1) == "processed"
    assert process_event(value.model_dump_json().encode(), offset=2) == "duplicate"
    with engine().connect() as connection:
        assert connection.scalar(select(func.count()).select_from(events)) == 1
    assert stream_status()["processed"] == 1
    assert kpis()["net_sales"] == before


def test_event_requires_aware_timestamps():
    body = event().model_dump()
    body["event_time"] = datetime(2011, 1, 1)
    with pytest.raises(ValidationError):
        TransactionEvent.model_validate(body)
