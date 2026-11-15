"""Reconcile existing source rows without rereading the Excel file."""

import json
import uuid
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy import select

from commerce.db import engine, pipeline_logs, quality, raw, sources, staging


def audit():
    with engine().begin() as connection:
        source = (
            connection.execute(
                select(sources).where(sources.c.complete.is_(True)).order_by(sources.c.imported_at.desc())
            )
            .mappings()
            .first()
        )
        if not source:
            raise ValueError("No completed source is available for audit")
        metrics = Counter()
        for disposition, issues in connection.execute(
            select(staging.c.disposition, staging.c.issues)
            .join(raw)
            .where(raw.c.source_id == source["source_id"])
        ):
            metrics["imported"] += 1
            metrics[disposition] += 1
            metrics.update(issue for issue in issues if issue != "duplicate")
        metrics["reconciled"] = int(
            metrics["imported"] == sum(metrics[x] for x in ("accepted", "quarantined", "duplicate"))
        )
        run_id, now = uuid.uuid4().hex, datetime.now(UTC)
        connection.execute(
            pipeline_logs.insert().values(
                run_id=run_id,
                started_at=now,
                ended_at=now,
                status="SUCCESS",
                details={**dict(metrics), "operation": "audit_existing_rows"},
            )
        )
        connection.execute(
            quality.insert(),
            [
                {"run_id": run_id, "metric": key, "value": value, "recorded_at": now}
                for key, value in metrics.items()
            ],
        )
    Path("artifacts/data_quality.json").write_text(json.dumps(dict(metrics), indent=2))
    print(json.dumps(dict(metrics), indent=2))


if __name__ == "__main__":
    audit()
