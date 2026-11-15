import json
from datetime import UTC, datetime
from pathlib import Path

from postgres_local import connection_url
from sqlalchemy import create_engine, text


def run():
    warehouse = create_engine(connection_url())
    with warehouse.connect() as connection:
        counts = (
            connection.execute(text(Path("sql/validation/reconciliation.sql").read_text())).mappings().one()
        )
        assert counts["raw_rows"] == counts["staged_rows"]
        assert counts["accepted_rows"] == counts["fact_rows"]
        assert (
            counts["raw_rows"]
            == counts["accepted_rows"] + counts["quarantined_rows"] + counts["duplicate_rows"]
        )
        fact = connection.execute(
            text(
                "select sum(amount) from (select amount from fact_sales_transactions union all select amount from fact_returns) t"
            )
        ).scalar()
        mart = connection.execute(text("select sum(net_sales) from analytics.mart_daily_sales")).scalar()
        assert fact == mart
        plan = connection.execute(text(Path("sql/validation/explain_postgres.sql").read_text())).scalar()
        models = (
            connection.execute(
                text(
                    "select table_name from information_schema.tables where table_schema='analytics' order by table_name"
                )
            )
            .scalars()
            .all()
        )
        version = connection.execute(text("select version()")).scalar()
    report = {
        "verified_at": datetime.now(UTC).isoformat(),
        "postgres_version": version,
        "counts": dict(counts),
        "fact_net_sales_gbp": str(fact),
        "dbt_net_sales_gbp": str(mart),
        "analytics_relations": models,
        "explain_analyze": plan,
    }
    Path("artifacts/postgres_verification.json").write_text(json.dumps(report, indent=2))
    print(json.dumps({k: v for k, v in report.items() if k != "explain_analyze"}, indent=2))


if __name__ == "__main__":
    run()
