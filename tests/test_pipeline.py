from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import func, select

from commerce.analytics import kpis
from commerce.db import engine, raw, sales, staging
from commerce.ingest import clean_record, customer_key, run_pipeline


def test_reconciliation_and_kpis(warehouse):
    values = kpis()
    assert values["gross_sales"] == pytest.approx(59.5)
    assert values["returns"] == 5
    assert values["net_sales"] == pytest.approx(54.5)
    assert values["orders"] == 4
    assert values["identifiable_customers"] == 2
    assert values["repeat_purchase_rate"] == 0.5
    assert values["data_label"] == "TEST FIXTURE"
    with engine().connect() as connection:
        assert connection.scalar(select(func.count()).select_from(raw)) == 9
        counts = dict(
            connection.execute(
                select(staging.c.disposition, func.count()).group_by(staging.c.disposition)
            ).all()
        )
    assert counts == {"accepted": 6, "duplicate": 1, "quarantined": 2}


def test_chunked_retry_is_idempotent(warehouse):
    first = kpis()
    result = run_pipeline(Path("data/fixtures/retail.csv"), fixture=True, chunk_size=3)
    assert result["imported"] == 9
    assert result["reconciled"] == 1
    assert kpis()["net_sales"] == first["net_sales"]
    with engine().connect() as connection:
        assert connection.scalar(select(func.count()).select_from(sales)) == 5


def test_decimal_returns_and_timezone(warehouse):
    row, issues, _ = clean_record(
        {
            "InvoiceNo": "C123",
            "StockCode": "12345A",
            "Quantity": 3,
            "InvoiceDate": "2011-06-01 12:00:00",
            "UnitPrice": ".335",
            "CustomerID": 42,
            "Country": "France",
        }
    )
    assert row["amount"] == Decimal("-1.01")
    assert row["event_time"].hour == 11
    assert "cancellation" in issues
    assert row["customer_key"] == customer_key("42.0")
    assert row["customer_key"] != "42"


@pytest.mark.parametrize(
    "field,value,issue",
    [
        ("Quantity", 0, "invalid_quantity"),
        ("Price", -1, "invalid_price"),
        ("Price", "NaN", "invalid_price"),
        ("InvoiceDate", "bad date", "invalid_date"),
        ("StockCode", "", "invalid_stock_code"),
    ],
)
def test_invalid_values_are_flagged(warehouse, field, value, issue):
    record = {
        "Invoice": "100",
        "StockCode": "12345",
        "Quantity": 1,
        "InvoiceDate": "2011-01-01 12:00:00",
        "Price": 2,
        "Customer ID": 42,
    }
    record[field] = value
    cleaned, issues, _ = clean_record(record)
    assert cleaned is None
    assert issue in issues


def test_filtered_kpis(warehouse):
    values = kpis(country="France")
    assert values["net_sales"] == 10
    assert values["orders"] == 1
    assert values["repeat_purchase_rate"] == 0


def test_customer_normalisation_does_not_truncate_fractional_ids(warehouse):
    assert customer_key("42.0") == customer_key(42)
    assert customer_key("42.5") != customer_key(42)
    assert customer_key("42.50") == customer_key("42.5")
    assert customer_key("NaN") is None


@pytest.mark.parametrize("timestamp", ["2011-03-27 01:30:00", "2011-10-30 01:30:00"])
def test_dst_ambiguity_is_quarantined(warehouse, timestamp):
    record = {
        "Invoice": "dst",
        "StockCode": "12345",
        "Quantity": 1,
        "InvoiceDate": timestamp,
        "Price": 2,
        "Customer ID": 42,
    }
    cleaned, issues, _ = clean_record(record)
    assert cleaned is None
    assert "invalid_date" in issues


def test_amount_overflow_is_quarantined(warehouse):
    record = {
        "Invoice": "overflow",
        "StockCode": "12345",
        "Quantity": 2_000_000_000,
        "InvoiceDate": "2011-01-01",
        "Price": "999999999999.00",
        "Customer ID": 42,
    }
    cleaned, issues, _ = clean_record(record)
    assert cleaned is None
    assert "invalid_amount" in issues


def test_all_portable_sql_executes(warehouse):
    from sqlalchemy import text

    paths = [x for x in Path("sql").rglob("*.sql") if "postgres" not in x.name]
    with engine().connect() as connection:
        for path in paths:
            connection.execute(text(path.read_text())).all()
