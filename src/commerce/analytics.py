from collections import Counter
from decimal import ROUND_HALF_UP, Decimal
from functools import lru_cache
from hashlib import sha256
from itertools import combinations
from pathlib import Path
from threading import Lock

import numpy as np
import pandas as pd
from sqlalchemy import func, select

from commerce.db import countries, engine, pipeline_logs, products, quality, returns, sales, sources

FRAME_LOCK = Lock()


def allocate_budget(budget, weights):
    """Conserve assumed budget to the penny using largest-remainder allocation."""
    cents = int((Decimal(str(budget)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    names = list(weights)
    values = [Decimal(str(weights[name])) for name in names]
    total = sum(values)
    if cents < 0 or not values or total <= 0 or any(not x.is_finite() or x < 0 for x in values):
        raise ValueError(
            "Nonnegative budget and finite nonnegative weights with a positive total are required"
        )
    quotas = [cents * value / total for value in values]
    allocated = [int(quota) for quota in quotas]
    remainder = cents - sum(allocated)
    priority = sorted(
        range(len(names)), key=lambda index: (-(quotas[index] - allocated[index]), names[index])
    )
    for index in priority[:remainder]:
        allocated[index] += 1
    return {
        "label": "HYPOTHETICAL BUDGET ALLOCATION — user-assumed priorities, not observed spending",
        "budget": float(Decimal(cents) / 100),
        "items": [
            {
                "segment": name,
                "assumed_weight": float(weights[name]),
                "allocated_budget": float(Decimal(amount) / 100),
            }
            for name, amount in zip(names, allocated, strict=True)
        ],
    }


def sales_frame(start=None, end=None, country=None, include_returns=True):
    with engine().connect() as connection:
        revision = connection.scalar(
            select(func.max(pipeline_logs.c.ended_at)).where(pipeline_logs.c.status == "SUCCESS")
        )
        provenance = connection.execute(select(sources.c.source_kind, sources.c.complete)).all()
    persist = bool(provenance) and all(kind != "TEST_FIXTURE" and complete for kind, complete in provenance)
    with FRAME_LOCK:
        frame = _sales_frame(str(engine().url), str(revision), persist)
    if start:
        frame = frame[frame.date_key >= pd.Timestamp(start)]
    if end:
        frame = frame[frame.date_key <= pd.Timestamp(end)]
    if country:
        frame = frame[frame.country == country]
    if not include_returns:
        frame = frame[frame.quantity > 0]
    return frame


@lru_cache(maxsize=1)
def _sales_frame(_database, _revision, persist):
    cache_key = sha256(f"{_database}:{_revision}:schema-v1".encode()).hexdigest()[:24]
    cache_path = Path(f"data/processed/analytics-{cache_key}.parquet")
    if persist and cache_path.exists():
        return pd.read_parquet(cache_path)
    columns = [
        "transaction_id",
        "invoice",
        "stock_code",
        "customer_key",
        "country",
        "date_key",
        "event_time",
        "quantity",
        "unit_price",
        "amount",
    ]

    def query(table):
        statement = select(*[table.c[x] for x in columns], products.c.description, products.c.category).join(
            products
        )
        return statement

    with engine().connect() as connection:
        frame = pd.read_sql(query(sales), connection)
        frame = pd.concat([frame, pd.read_sql(query(returns), connection)], ignore_index=True)
    if not frame.empty:
        frame["event_time"] = pd.to_datetime(frame.event_time, utc=True)
        frame["date_key"] = pd.to_datetime(frame.date_key)
        frame["amount"] = frame.amount.astype(float)
        if persist:
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            temporary = cache_path.with_suffix(".part")
            frame.to_parquet(temporary, index=False)
            temporary.replace(cache_path)
    return frame


def kpis(start=None, end=None, country=None):
    def aggregate(table):
        query = select(
            func.coalesce(func.sum(table.c.amount), 0),
            func.count(),
            func.count(func.distinct(table.c.invoice)),
            func.count(func.distinct(table.c.customer_key)),
        )
        if start:
            query = query.where(table.c.date_key >= start)
        if end:
            query = query.where(table.c.date_key <= end)
        if country:
            query = query.where(table.c.country == country)
        with engine().connect() as connection:
            return connection.execute(query).one()

    gross, lines, orders, customer_count = aggregate(sales)
    returned, return_lines, _, _ = aggregate(returns)
    counts_query = select(sales.c.customer_key, func.count(func.distinct(sales.c.invoice)).label("orders"))
    if start:
        counts_query = counts_query.where(sales.c.date_key >= start)
    if end:
        counts_query = counts_query.where(sales.c.date_key <= end)
    if country:
        counts_query = counts_query.where(sales.c.country == country)
    counts_query = counts_query.where(sales.c.customer_key.is_not(None)).group_by(sales.c.customer_key)
    with engine().connect() as connection:
        counts = list(connection.execute(counts_query))
        provenance = [dict(x._mapping) for x in connection.execute(select(sources))]
        extent = connection.execute(select(func.min(sales.c.date_key), func.max(sales.c.date_key))).one()
        available_countries = list(
            connection.scalars(select(countries.c.country).order_by(countries.c.country))
        )
    return {
        "gross_sales": float(gross),
        "returns": float(-returned),
        "net_sales": float(gross + returned),
        "orders": orders,
        "identifiable_customers": customer_count,
        "sales_lines": lines,
        "return_lines": return_lines,
        "average_order_value": float(gross / orders) if orders else 0,
        "repeat_purchase_rate": sum(row.orders > 1 for row in counts) / len(counts) if counts else 0,
        "currency": "GBP",
        "data_label": "TEST FIXTURE"
        if any(x["source_kind"] == "TEST_FIXTURE" for x in provenance)
        else "UCI MIRROR · 2009–2011"
        if any(x["source_kind"] == "UCI_MIRROR" for x in provenance)
        else "UCI HISTORICAL · 2009–2011",
        "sources": provenance,
        "date_min": extent[0],
        "date_max": extent[1],
        "countries": available_countries,
    }


def trends(frame, frequency="D"):
    if frame.empty:
        return pd.DataFrame(columns=["date", "net_sales", "rolling_7d", "orders"])
    grouped = frame.set_index("date_key").resample(frequency)
    result = grouped.agg(net_sales=("amount", "sum"), orders=("invoice", "nunique")).reset_index()
    result = result.rename(columns={"date_key": "date"})
    result["rolling_7d"] = result.net_sales.rolling(7, min_periods=1).mean()
    return result


def rfm(frame, as_of=None):
    paid = frame[(frame.quantity > 0) & frame.customer_key.notna()].copy()
    if paid.empty:
        return pd.DataFrame(columns=["customer_key", "recency", "frequency", "monetary", "segment"])
    reference = pd.Timestamp(as_of) if as_of else paid.date_key.max() + pd.Timedelta(days=1)
    result = (
        paid.groupby("customer_key")
        .agg(
            last_purchase=("date_key", "max"),
            first_purchase=("date_key", "min"),
            frequency=("invoice", "nunique"),
            monetary=("amount", "sum"),
            product_diversity=("stock_code", "nunique"),
        )
        .reset_index()
    )
    result["recency"] = (reference - result.last_purchase).dt.days
    result["average_order_value"] = result.monetary / result.frequency
    # Percentile-based scoring avoids arbitrary tie breaking for equal-valued customers.
    for name, ascending in (("recency", False), ("frequency", True), ("monetary", True)):
        result[f"{name}_score"] = (
            np.ceil(result[name].rank(method="max", pct=True, ascending=ascending) * 5).clip(1, 5).astype(int)
        )
    result["segment"] = np.select(
        [
            (result.recency_score >= 4) & (result.frequency_score >= 4),
            (result.recency_score <= 2) & (result.monetary_score >= 4),
            result.frequency >= 3,
            result.recency_score >= 4,
        ],
        ["Champions", "At risk · high value", "Loyal", "New / recent"],
        default="Developing",
    )
    return result


def retention(frame):
    paid = frame[(frame.quantity > 0) & frame.customer_key.notna()].copy()
    if paid.empty:
        return pd.DataFrame(columns=["cohort", "period", "customers", "cohort_size", "retention_rate"])
    paid["month"] = paid.date_key.dt.to_period("M")
    paid["cohort"] = paid.groupby("customer_key")["month"].transform("min")
    paid["period"] = (
        (paid.month.dt.year - paid.cohort.dt.year) * 12 + paid.month.dt.month - paid.cohort.dt.month
    )
    result = paid.groupby(["cohort", "period"]).customer_key.nunique().rename("customers").reset_index()
    sizes = result[result.period == 0].set_index("cohort").customers
    result["cohort_size"] = result.cohort.map(sizes)
    result["retention_rate"] = result.customers / result.cohort_size
    result["cohort"] = result.cohort.astype(str)
    return result


def product_performance(frame):
    if frame.empty:
        return pd.DataFrame(
            columns=["stock_code", "description", "net_sales", "units", "return_units", "orders"]
        )
    result = (
        frame.groupby(["stock_code", "description"], dropna=False)
        .agg(
            net_sales=("amount", "sum"),
            units=("quantity", lambda x: x[x > 0].sum()),
            return_units=("quantity", lambda x: -x[x < 0].sum()),
            orders=("invoice", "nunique"),
        )
        .reset_index()
    )
    result["return_unit_rate"] = result.return_units / result.units.replace(0, np.nan)
    return result.sort_values("net_sales", ascending=False).fillna(0)


def basket_rules(frame, min_support=0.002, max_products=60):
    paid = frame[(frame.quantity > 0) & (frame.category == "merchandise")]
    top = paid.groupby("stock_code").invoice.nunique().nlargest(max_products).index
    baskets = paid.groupby("invoice").stock_code.agg(lambda x: set(x) & set(top))
    count = len(baskets)
    singles, pairs = Counter(), Counter()
    for basket in baskets:
        singles.update(basket)
        pairs.update(combinations(sorted(basket), 2))
    result = []
    for (left, right), occurrences in pairs.items():
        support = occurrences / count
        if support < min_support:
            continue
        for a, b in ((left, right), (right, left)):
            confidence = occurrences / singles[a]
            result.append(
                {
                    "antecedent": a,
                    "consequent": b,
                    "basket_count": occurrences,
                    "support": support,
                    "confidence": confidence,
                    "lift": confidence / (singles[b] / count),
                }
            )
    return sorted(result, key=lambda x: (x["lift"], x["support"]), reverse=True)[:100]


def scenario(audience, budget, response_rate, incremental_rate, order_value, contribution_rate):
    expected_orders = audience * response_rate * incremental_rate
    revenue = expected_orders * order_value
    contribution = revenue * contribution_rate
    return {
        "label": "HYPOTHETICAL SCENARIO · assumptions, not observed outcomes",
        "audience": audience,
        "expected_incremental_orders": expected_orders,
        "estimated_incremental_revenue": revenue,
        "assumed_contribution_before_spend": contribution,
        "net_contribution_after_spend": contribution - budget,
        "break_even_incremental_orders": budget / (order_value * contribution_rate)
        if contribution_rate
        else None,
        "assumptions": {
            "budget": budget,
            "response_rate": response_rate,
            "incremental_rate": incremental_rate,
            "order_value": order_value,
            "contribution_rate": contribution_rate,
        },
    }


def quality_status():
    with engine().connect() as connection:
        runs = [
            dict(x._mapping)
            for x in connection.execute(
                select(pipeline_logs).order_by(pipeline_logs.c.started_at.desc()).limit(20)
            )
        ]
        if not runs:
            return {"runs": [], "metrics": {}, "label": "No pipeline run yet"}
        last_success = next((x for x in runs if x["status"] == "SUCCESS"), None)
        metrics = (
            dict(
                connection.execute(
                    select(quality.c.metric, quality.c.value).where(
                        quality.c.run_id == last_success["run_id"]
                    )
                ).all()
            )
            if last_success
            else {}
        )
    return {
        "runs": runs,
        "metrics": metrics,
        "label": "Source dates are historical; ingestion time is operational freshness",
    }
