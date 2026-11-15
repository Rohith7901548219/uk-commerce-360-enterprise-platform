"""Auditable, chunked source acquisition and warehouse loading."""

import hashlib
import hmac
import json
import logging
import re
import urllib.request
import uuid
import zipfile
from collections import Counter
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from pytz import AmbiguousTimeError, NonExistentTimeError
from sqlalchemy import func, select, update

from commerce.config import settings
from commerce.db import (
    activity,
    countries,
    customers,
    dates,
    engine,
    initialize,
    insert_ignore,
    pipeline_logs,
    products,
    quality,
    raw,
    returns,
    sales,
    sources,
    staging,
)

LOGGER = logging.getLogger(__name__)
SOURCE_URL = "https://archive.ics.uci.edu/static/public/502/online+retail+ii.zip"
ALIASES = {
    "invoiceno": "invoice",
    "invoice": "invoice",
    "stockcode": "stock_code",
    "description": "description",
    "quantity": "quantity",
    "invoicedate": "event_time",
    "price": "unit_price",
    "unitprice": "unit_price",
    "customerid": "customer_id",
    "country": "country",
}


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def download_data() -> Path:
    settings()
    destination = Path("data/raw/online_retail_II.xlsx")
    if not destination.exists():
        archive = Path("data/raw/source.zip.part")
        request = urllib.request.Request(SOURCE_URL, headers={"User-Agent": "UKCommerce360/0.1 portfolio"})
        with urllib.request.urlopen(request, timeout=180) as response, archive.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        with zipfile.ZipFile(archive) as bundle:
            matches = [x for x in bundle.namelist() if x.lower().endswith(".xlsx")]
            if len(matches) != 1:
                raise ValueError("Expected exactly one workbook in the official UCI archive")
            with bundle.open(matches[0]) as source, destination.with_suffix(".part").open("wb") as output:
                while chunk := source.read(1024 * 1024):
                    output.write(chunk)
        destination.with_suffix(".part").replace(destination)
        archive.unlink()
    checksum = hashlib.file_digest(destination.open("rb"), "sha256").hexdigest()
    manifest = {
        "url": SOURCE_URL,
        "sha256": checksum,
        "bytes": destination.stat().st_size,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "licence": "CC BY 4.0",
        "attribution": "Chen, D. (2012). Online Retail II. UCI. doi:10.24432/C5CG6D",
    }
    manifest_path = destination.with_suffix(".manifest.json")
    if manifest_path.exists():
        previous = json.loads(manifest_path.read_text())
        if previous["sha256"] != checksum:
            raise ValueError("Source checksum changed; preserve and investigate the original workbook")
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return destination


def customer_key(value) -> str | None:
    if value is None or str(value).strip().lower() in ("", "nan", "none", "null", "<na>"):
        return None
    secret = settings().customer_hash_key
    if not secret:
        raise ValueError("CUSTOMER_HASH_KEY is required; run scripts/setup.ps1 or commerce bootstrap")
    try:
        number = Decimal(str(value))
        canonical = (
            str(int(number))
            if number.is_finite() and number == number.to_integral_value()
            else str(number.normalize())
        )
    except (ValueError, InvalidOperation):
        canonical = str(value).strip()
    return hmac.new(secret.encode(), canonical.encode(), "sha256").hexdigest()[:24]


def clean_record(record: dict) -> tuple[dict | None, list[str], str]:
    row = {ALIASES.get(re.sub(r"[^a-z]", "", str(k).lower()), str(k)): v for k, v in record.items()}
    issues = []
    invoice = str(row.get("invoice") or "").strip()
    stock = str(row.get("stock_code") or "").strip().upper()
    if not invoice:
        issues.append("missing_invoice")
    if not stock or not re.fullmatch(r"[A-Z0-9][A-Z0-9 ._/-]{0,29}", stock):
        issues.append("invalid_stock_code")
    description = str(row.get("description") or "Unknown product").strip()
    if description == "Unknown product":
        issues.append("missing_description")
    category = "merchandise" if re.fullmatch(r"\d{5}[A-Z]{0,2}", stock) else "non_merchandise"
    if category == "non_merchandise":
        issues.append("non_merchandise_code")
    try:
        quantity_decimal = Decimal(str(row.get("quantity")))
        if not quantity_decimal.is_finite() or quantity_decimal != quantity_decimal.to_integral_value():
            raise ValueError("Quantity must be a finite integer")
        quantity = int(quantity_decimal)
        if quantity == 0 or abs(quantity) > 2_147_483_647:
            raise ValueError("Quantity out of range")
    except (ValueError, InvalidOperation, TypeError):
        quantity = 0
        issues.append("invalid_quantity")
    try:
        price = Decimal(str(row.get("unit_price"))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
        if not price.is_finite() or price <= 0 or price >= Decimal("1000000000000"):
            raise ValueError("Price must be positive")
    except (ValueError, InvalidOperation):
        price = Decimal(0)
        issues.append("invalid_price")
    try:
        timestamp = pd.Timestamp(row.get("event_time"))
        if pd.isna(timestamp):
            raise ValueError("Missing date")
        if timestamp.tzinfo is None:
            timestamp = timestamp.tz_localize("Europe/London", ambiguous="raise", nonexistent="raise")
        local_date = timestamp.tz_convert("Europe/London").date()
        timestamp = timestamp.tz_convert("UTC").to_pydatetime()
    except (ValueError, TypeError, OverflowError, AmbiguousTimeError, NonExistentTimeError):
        timestamp, local_date = None, None
        issues.append("invalid_date")
    customer = customer_key(row.get("customer_id"))
    if customer is None:
        issues.append("missing_customer")
    country = str(row.get("country") or "Unknown").strip()
    if country == "Unknown":
        issues.append("missing_country")
    cancellation = invoice.upper().startswith("C")
    if cancellation:
        issues.append("cancellation")
    is_return = quantity < 0 or cancellation
    if is_return:
        issues.append("return")
        quantity = -abs(quantity)
    canonical = [
        invoice,
        stock,
        str(row.get("quantity")),
        str(row.get("unit_price")),
        str(row.get("event_time")),
        str(row.get("customer_id")),
        country,
        description,
    ]
    fingerprint = digest(json.dumps(canonical, default=str))
    fatal = {"missing_invoice", "invalid_stock_code", "invalid_quantity", "invalid_price", "invalid_date"}
    if fatal.intersection(issues):
        return None, issues, fingerprint
    amount = (quantity * price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if abs(amount) >= Decimal("10000000000000000"):
        issues.append("invalid_amount")
        return None, issues, fingerprint
    return (
        {
            "invoice": invoice,
            "stock_code": stock,
            "description": description,
            "category": category,
            "customer_key": customer,
            "country": country,
            "quantity": quantity,
            "unit_price": price,
            "event_time": timestamp,
            "date_key": local_date,
            "amount": amount,
        },
        issues,
        fingerprint,
    )


def _load_chunk(source_id, sheet, records, seen):
    now = datetime.now(UTC)
    with engine().begin() as connection:
        ids = [digest(f"{source_id}:{sheet}:{index}") for index, _ in records]
        existing = set(connection.scalars(select(raw.c.raw_id).where(raw.c.raw_id.in_(ids))))
        raw_rows, staged, valid_sales, valid_returns = [], [], [], []
        dim_c, dim_p, dim_g, dim_d = {}, {}, {}, {}
        for (index, record), raw_id in zip(records, ids, strict=True):
            if raw_id in existing:
                continue
            raw_rows.append(
                {
                    "raw_id": raw_id,
                    "source_id": source_id,
                    "sheet": sheet,
                    "row_number": index,
                    "payload": json.loads(json.dumps(record, default=str)),
                    "ingestion_time": now,
                }
            )
            cleaned, issues, fingerprint = clean_record(record)
            disposition = "accepted" if cleaned else "quarantined"
            if fingerprint in seen:
                issues.append("duplicate")
                disposition = "duplicate"
            seen.add(fingerprint)
            staged.append(
                {"raw_id": raw_id, "fingerprint": fingerprint, "disposition": disposition, "issues": issues}
            )
            if disposition != "accepted":
                continue
            if cleaned["customer_key"]:
                dim_c[cleaned["customer_key"]] = {"customer_key": cleaned["customer_key"]}
            dim_p[cleaned["stock_code"]] = {k: cleaned[k] for k in ("stock_code", "description", "category")}
            dim_g[cleaned["country"]] = {"country": cleaned["country"]}
            day = cleaned["date_key"]
            dim_d[day] = {"date_key": day, "year": day.year, "month": day.month, "weekday": day.weekday()}
            fact_row = {k: v for k, v in cleaned.items() if k not in ("description", "category")}
            fact_row["transaction_id"] = raw_id
            (valid_returns if "return" in issues else valid_sales).append(fact_row)
        insert_ignore(connection, raw, raw_rows)
        insert_ignore(connection, staging, staged)
        for table, values in ((customers, dim_c), (products, dim_p), (countries, dim_g), (dates, dim_d)):
            insert_ignore(connection, table, list(values.values()))
        insert_ignore(connection, sales, valid_sales)
        insert_ignore(connection, returns, valid_returns)


def run_pipeline(path: Path, fixture=False, chunk_size=5000, mirrored=False) -> dict:
    initialize()
    source_id = hashlib.file_digest(path.open("rb"), "sha256").hexdigest()
    run_id = uuid.uuid4().hex
    started = datetime.now(UTC)
    with engine().begin() as connection:
        insert_ignore(
            connection,
            sources,
            [
                {
                    "source_id": source_id,
                    "filename": path.name,
                    "source_kind": "TEST_FIXTURE"
                    if fixture
                    else "UCI_MIRROR"
                    if mirrored
                    else "UCI_HISTORICAL",
                    "imported_at": started,
                    "rows_imported": 0,
                    "complete": False,
                }
            ],
        )
        connection.execute(pipeline_logs.insert().values(run_id=run_id, status="RUNNING", started_at=started))
        seen = set(connection.scalars(select(staging.c.fingerprint)))
    try:
        if path.suffix.lower() == ".csv":
            sheets = [("fixture", pd.read_csv(path, dtype=object, keep_default_na=False).to_dict("records"))]
        else:
            workbook = load_workbook(path, read_only=True, data_only=True)

            def sheet_rows(sheet):
                iterator = sheet.iter_rows(values_only=True)
                headers = next(iterator)
                if not {"Invoice", "InvoiceNo"}.intersection(headers):
                    raise ValueError(f"Unknown source headers in {sheet.title}: {headers}")
                for values in iterator:
                    yield dict(zip(headers, values, strict=True))

            sheets = [(sheet.title, sheet_rows(sheet)) for sheet in workbook.worksheets]
        for sheet, records in sheets:
            chunk = []
            for index, record in enumerate(records, 2):
                chunk.append((index, record))
                if len(chunk) >= chunk_size:
                    _load_chunk(source_id, sheet, chunk, seen)
                    LOGGER.info(json.dumps({"sheet": sheet, "row": index, "run_id": run_id}))
                    chunk = []
            _load_chunk(source_id, sheet, chunk, seen)
        if path.suffix.lower() != ".csv":
            workbook.close()
        metrics = Counter()
        with engine().begin() as connection:
            query = (
                select(staging.c.disposition, staging.c.issues).join(raw).where(raw.c.source_id == source_id)
            )
            for disposition, issues in connection.execute(query):
                metrics["imported"] += 1
                metrics[disposition] += 1
                metrics.update(issue for issue in issues if issue != "duplicate")
            metrics["reconciled"] = int(
                metrics["imported"] == sum(metrics[x] for x in ("accepted", "quarantined", "duplicate"))
            )
            connection.execute(
                quality.insert(),
                [
                    {"run_id": run_id, "metric": k, "value": v, "recorded_at": datetime.now(UTC)}
                    for k, v in metrics.items()
                ],
            )
            connection.execute(
                update(sources)
                .where(sources.c.source_id == source_id)
                .values(complete=True, rows_imported=metrics["imported"])
            )
            connection.execute(
                update(pipeline_logs)
                .where(pipeline_logs.c.run_id == run_id)
                .values(status="SUCCESS", ended_at=datetime.now(UTC), details=dict(metrics))
            )
            # Incrementally rebuild customer order activity from accepted facts, not source rows.
            connection.execute(activity.delete())
            connection.execute(
                activity.insert().from_select(
                    ["customer_key", "invoice", "event_time", "amount", "product_count"],
                    select(
                        sales.c.customer_key,
                        sales.c.invoice,
                        func.min(sales.c.event_time),
                        func.sum(sales.c.amount),
                        func.count(func.distinct(sales.c.stock_code)),
                    )
                    .where(sales.c.customer_key.is_not(None))
                    .group_by(sales.c.customer_key, sales.c.invoice),
                )
            )
        if not fixture:
            Path("artifacts/data_quality.json").write_text(
                json.dumps(dict(metrics), indent=2), encoding="utf-8"
            )
        return dict(metrics)
    except Exception as error:
        with engine().begin() as connection:
            connection.execute(
                update(pipeline_logs)
                .where(pipeline_logs.c.run_id == run_id)
                .values(
                    status="FAILED",
                    ended_at=datetime.now(UTC),
                    details={
                        "error_type": type(error).__name__,
                        "message": "Pipeline failed; review protected local execution logs.",
                    },
                )
            )
        raise
