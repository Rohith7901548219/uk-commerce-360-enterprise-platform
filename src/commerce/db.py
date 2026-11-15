from functools import lru_cache

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    event,
)

from commerce.config import settings

metadata = MetaData()
sources = Table(
    "source_files",
    metadata,
    Column("source_id", String(64), primary_key=True),
    Column("filename", String(250)),
    Column("source_kind", String(30), nullable=False),
    Column("imported_at", DateTime(timezone=True)),
    Column("rows_imported", Integer, default=0),
    Column("complete", Boolean, default=False),
)
raw = Table(
    "raw_retail_transactions",
    metadata,
    Column("raw_id", String(64), primary_key=True),
    Column("source_id", ForeignKey("source_files.source_id"), nullable=False),
    Column("sheet", String(100)),
    Column("row_number", Integer),
    Column("payload", JSON, nullable=False),
    Column("ingestion_time", DateTime(timezone=True), nullable=False),
    UniqueConstraint("source_id", "sheet", "row_number"),
)
staging = Table(
    "stg_retail_transactions",
    metadata,
    Column("raw_id", ForeignKey("raw_retail_transactions.raw_id"), primary_key=True),
    Column("fingerprint", String(64), index=True),
    Column("disposition", String(20), nullable=False),
    Column("issues", JSON, nullable=False),
)
customers = Table("dim_customer", metadata, Column("customer_key", String(32), primary_key=True))
products = Table(
    "dim_product",
    metadata,
    Column("stock_code", String(30), primary_key=True),
    Column("description", Text),
    Column("category", String(30), nullable=False),
)
countries = Table("dim_country", metadata, Column("country", String(100), primary_key=True))
dates = Table(
    "dim_date",
    metadata,
    Column("date_key", Date, primary_key=True),
    Column("year", Integer),
    Column("month", Integer),
    Column("weekday", Integer),
)


def fact(name):
    return Table(
        name,
        metadata,
        Column("transaction_id", ForeignKey("raw_retail_transactions.raw_id"), primary_key=True),
        Column("invoice", String(40), nullable=False, index=True),
        Column("stock_code", ForeignKey("dim_product.stock_code"), nullable=False),
        Column("customer_key", ForeignKey("dim_customer.customer_key"), index=True),
        Column("country", ForeignKey("dim_country.country"), nullable=False),
        Column("date_key", ForeignKey("dim_date.date_key"), nullable=False, index=True),
        Column("event_time", DateTime(timezone=True), nullable=False, index=True),
        Column("quantity", Integer, nullable=False),
        Column("unit_price", Numeric(18, 4), nullable=False),
        Column("amount", Numeric(18, 2), nullable=False),
    )


sales = fact("fact_sales_transactions")
returns = fact("fact_returns")
activity = Table(
    "fact_customer_activity",
    metadata,
    Column("customer_key", ForeignKey("dim_customer.customer_key"), primary_key=True),
    Column("invoice", String(40), primary_key=True),
    Column("event_time", DateTime(timezone=True)),
    Column("amount", Numeric(18, 2)),
    Column("product_count", Integer),
)
quality = Table(
    "data_quality_results",
    metadata,
    Column("run_id", String(64), primary_key=True),
    Column("metric", String(80), primary_key=True),
    Column("value", Integer, nullable=False),
    Column("recorded_at", DateTime(timezone=True)),
)
pipeline_logs = Table(
    "pipeline_execution_logs",
    metadata,
    Column("run_id", String(64), primary_key=True),
    Column("status", String(20)),
    Column("started_at", DateTime(timezone=True)),
    Column("ended_at", DateTime(timezone=True)),
    Column("details", JSON),
)
model_logs = Table(
    "model_execution_logs",
    metadata,
    Column("run_id", String(64), primary_key=True),
    Column("model_type", String(40)),
    Column("trained_at", DateTime(timezone=True)),
    Column("metrics", JSON),
    Column("artifact", Text),
)
predictions = Table(
    "mart_customer_predictions",
    metadata,
    Column("customer_key", ForeignKey("dim_customer.customer_key"), primary_key=True),
    Column("as_of", DateTime(timezone=True)),
    Column("probability", Numeric(10, 8)),
    Column("model_run", String(64)),
)
forecasts = Table(
    "mart_revenue_forecasts",
    metadata,
    Column("forecast_date", Date, primary_key=True),
    Column("prediction", Numeric(18, 2)),
    Column("lower", Numeric(18, 2)),
    Column("upper", Numeric(18, 2)),
    Column("model", String(50)),
)
events = Table(
    "stream_events",
    metadata,
    Column("event_id", String(64), primary_key=True),
    Column("source", String(40)),
    Column("event_time", DateTime(timezone=True)),
    Column("replay_time", DateTime(timezone=True)),
    Column("ingestion_time", DateTime(timezone=True)),
    Column("status", String(20)),
    Column("topic", String(100)),
    Column("partition_id", Integer),
    Column("offset_id", Integer),
    Column("payload", JSON),
    UniqueConstraint("topic", "partition_id", "offset_id"),
)
stream_state = Table(
    "stream_runtime",
    metadata,
    Column("key", String(50), primary_key=True),
    Column("value", JSON),
    Column("updated_at", DateTime(timezone=True)),
)
Index("ix_sales_customer_time", sales.c.customer_key, sales.c.event_time)


@lru_cache
def engine():
    url = settings().database_url
    options = (
        {"connect_args": {"check_same_thread": False, "timeout": 60}} if url.startswith("sqlite") else {}
    )
    result = create_engine(url, pool_pre_ping=True, **options)
    if url.startswith("sqlite"):

        @event.listens_for(result, "connect")
        def sqlite_config(connection, _):
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")

    return result


def initialize():
    metadata.create_all(engine())


def insert_ignore(connection, table, rows):
    if not rows:
        return
    if connection.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    connection.execute(insert(table).on_conflict_do_nothing(), rows)
