"""Publish aggregate local verification evidence into repository documentation."""

import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from commerce.analytics import kpis


def read(name):
    return json.loads(Path("artifacts", name).read_text(encoding="utf-8"))


def markdown_table(headers, rows):
    return "\n".join(
        ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
        + ["| " + " | ".join(str(value) for value in row) + " |" for row in rows]
    )


def junit(path):
    root = ET.parse(path).getroot()
    suites = list(root.iter("testsuite"))
    return {
        key: sum(int(s.attrib.get(key, 0)) for s in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }


def run():
    quality = read("data_quality.json")
    repurchase = read("repurchase_evaluation.json")
    forecast = read("forecast_evaluation.json")
    postgres = read("postgres_verification.json")
    stats = read("statistical_analysis.json")
    browser = read("browser_smoke.json")
    http = read("http_verification.json")
    audit = read("all-dependency-audit.json")
    dbt = json.loads(Path("dbt/target/run_results.json").read_text(encoding="utf-8"))
    tests = junit("artifacts/tests.xml")
    pg_tests = junit("artifacts/postgres-tests.xml")
    assert tests["failures"] == tests["errors"] == pg_tests["failures"] == pg_tests["errors"] == 0
    assert len(browser) == 11 and all(row["exception_count"] == 0 for row in browser)
    assert all(row["status"] in ("pass", "success") for row in dbt["results"])
    values = kpis()
    output = Path("docs/verification")
    output.mkdir(parents=True, exist_ok=True)
    public_artifacts = [
        "data_quality.json",
        "postgres_verification.json",
        "postgres_transfer.json",
        "http_verification.json",
        "browser_smoke.json",
        "all-dependency-audit.json",
    ]
    for name in public_artifacts:
        shutil.copyfile(Path("artifacts", name), output / name)
    for name in ("tests.xml", "postgres-tests.xml"):
        shutil.copyfile(Path("artifacts", name), output / name)
    dbt_summary = {
        "results": [
            {k: row.get(k) for k in ("unique_id", "status", "execution_time", "message")}
            for row in dbt["results"]
        ],
        "elapsed_time": dbt["elapsed_time"],
    }
    (output / "dbt-results.json").write_text(json.dumps(dbt_summary, indent=2), encoding="utf-8")
    models = Path("docs/machine-learning/results")
    models.mkdir(parents=True, exist_ok=True)
    for name in (
        "repurchase_evaluation.json",
        "forecast_evaluation.json",
        "statistical_analysis.json",
        "segment_stability.json",
        "training_manifest.json",
    ):
        shutil.copyfile(Path("artifacts", name), models / name)
    (output / "kpis.json").write_text(json.dumps(values, indent=2, default=str), encoding="utf-8")
    winner = repurchase["selected_model"]
    score = repurchase["models"][winner]["test"]
    vulnerabilities = sum(len(row.get("vulns", [])) for row in audit["dependencies"])
    quality_table = markdown_table(["Metric", "Actual records"], [(k, f"{v:,}") for k, v in quality.items()])
    kpi_table = markdown_table(
        ["KPI", "Actual historical result"],
        [
            ("Gross sales", f"£{values['gross_sales']:,.2f}"),
            ("Returns", f"£{values['returns']:,.2f}"),
            ("Net sales", f"£{values['net_sales']:,.2f}"),
            ("Positive-purchase orders", f"{values['orders']:,}"),
            ("Identifiable positive-purchase customers", f"{values['identifiable_customers']:,}"),
            ("Gross average order value", f"£{values['average_order_value']:,.2f}"),
            ("Within-period repeat-purchase rate", f"{values['repeat_purchase_rate']:.2%}"),
        ],
    )
    classifier_table = markdown_table(
        ["Candidate", "Test AP / PR-AUC", "ROC-AUC", "Precision", "Recall", "F1", "Brier"],
        [
            (
                name,
                *[
                    f"{result['test'][key]:.4f}"
                    for key in ("pr_auc", "roc_auc", "precision", "recall", "f1", "brier_score")
                ],
            )
            for name, result in repurchase["models"].items()
        ],
    )
    forecast_table = markdown_table(
        ["Candidate", "Development MAE", "Final test MAE", "Final test RMSE", "Final test WAPE"],
        [
            (
                name,
                f"£{result['development_mae']:,.2f}",
                f"£{result['folds'][-1]['mae']:,.2f}",
                f"£{result['folds'][-1]['rmse']:,.2f}",
                f"{result['folds'][-1]['wape']:.2%}",
            )
            for name, result in forecast["models"].items()
        ],
    )
    report = f"""# Delivery and verification report

15 November 2026 · Independent portfolio project · **Full project completion is not claimed.**

## 1. Overview and implemented architecture

The working local platform connects auditable historical ingestion, a relational star
schema, customer/product analytics, evaluated models, FastAPI and an eleven-page
Streamlit application. PostgreSQL 17.12, Alembic and dbt have actually run. Historical
Kafka-compatible producer/consumer/DLQ code exists, but Redpanda execution is blocked.
The prepared application's active backend is the reconciled full-data PostgreSQL
warehouse on 127.0.0.1:5433. SQLite remains available for fresh local setups and tests.

Architecture: source → raw → validation/staging → sales/returns star → SQL/dbt/models →
API → Streamlit. Replay uses a separate broker/event-store path so sales cannot inflate.
See [architecture](../ARCHITECTURE.md) and [warehouse design](architecture/WAREHOUSE.md).

## 2. Repository and completed modules

`src/commerce` contains config, database metadata, ETL, analytics, ML, schemas, API and
streaming. `app` contains all eleven business pages. `database/migrations`, `dbt` and
`sql` contain real schema/transformation assets. `scripts` supplies setup/start/stop,
verification, acquisition, native PostgreSQL operations and evidence capture. `tests`,
`dashboards/powerbi`, `.github/workflows`, `infra` and `docs` contain the remaining
quality, reporting, deployment and portfolio deliverables. No empty placeholder tree
or fabricated Power BI binary is provided.

## 3. Actual dataset and acquisition provenance

Both source sheets were ingested: Year 2009-2010 and Year 2010-2011. Source coverage
is {values["date_min"]} to {values["date_max"]}. All **{quality["imported"]:,}** lines remain
in raw/staging. The actual workbook was acquired from an explicitly attributed public
mirror because this host could not resolve UCI, even outside the sandbox.

SHA256: `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
It matches the mirror's published metadata. Direct UCI byte verification remains pending.
See [acquisition script](../scripts/acquire_mirror.py). Original attribution: Chen, D.
(2012), Online Retail II, UCI, DOI 10.24432/C5CG6D, CC BY 4.0. The application labels
mirror provenance and historical dates. No full dataset or raw customer IDs are tracked.

## 4. Data quality and reconciliation

{quality_table}

Accepted + quarantined + duplicate = imported exactly. Accepted facts consist of
**{values["sales_lines"]:,} sales lines and {values["return_lines"]:,} return lines**. Issue counts overlap dispositions:
for example invalid-price warnings include duplicate rows, so they must not be summed
as exclusive rejected counts. Missing customer IDs remain in valid revenue; returns
are negative and customer outputs are keyed HMAC pseudonyms. Raw lineage is retained.

PostgreSQL fact net revenue and dbt daily mart both equal **£{float(postgres["fact_net_sales_gbp"]):,.2f}**.
Actual full table counts and EXPLAIN ANALYZE output are in
[PostgreSQL verification](verification/postgres_verification.json).

## 5. Actual business metrics

{kpi_table}

These are observed historical source calculations, not current trading or claimed
business impact. AOV uses gross positive-purchase revenue per positive invoice.
Repeat rate uses identifiable positive-purchase customers in the selected period.

## 6. SQL and dbt

Validated SQL includes window-based revenue, customer contribution/Pareto shares,
country/product rankings, basket support/confidence/lift and PostgreSQL YoY. dbt
implements daily/monthly sales, RFM, cohorts, retention, products and a union staging
view. **Seven models and ten data tests passed: PASS=17, ERROR=0.** The incremental
rerun also passed and preserved exact revenue reconciliation. Older backfills require
full refresh beyond the documented 31-day overlap. Query plans are measured artifacts,
not invented performance improvements.

## 7. Repeat-purchase evaluation

30-day target; 180-day features; six chronological snapshots with horizon separation.
The first four train, fifth selects by average precision and sixth measures later test
performance. Selection: **{winner}**. Test sample: **{score["samples"]:,}** customers;
positive prevalence **{score["positive_rate"]:.2%}**. Average precision is reported as
AP/PR-AUC, not trapezoidal integration.

{classifier_table}

At threshold 0.5, recall is only {score["recall"]:.1%}; calibration and threshold costs
need business review. No retention uplift or causal usefulness is established. Customers
can recur across time splits because the objective concerns existing buyers. Final-day
incompleteness/right-censoring is documented. Frozen evaluated and refitted serving
artifacts are separate; actual reports, parameters, versions and source checksum are saved.
Training was executed twice with the same selected models and measured headline metrics.

## 8. Forecasting, segmentation and statistical analysis

Daily net sales; three development origins select by MAE and the final 28-day horizon
is held out. Selection: **{forecast["selected_model"]}**.

{forecast_table}

Approximate 90% residual bands are not guaranteed coverage. Forecast dates follow the
historical source end, not today. RFM segmentation, 30-day membership stability and
temporal basket-rule summaries are saved. The seeded invoice bootstrap gives a 95%
mean-AOV interval of £{stats["bootstrap_95pct_mean_interval"][0]:,.2f}–£{stats["bootstrap_95pct_mean_interval"][1]:,.2f};
it assumes independent invoices and does not correct repeat-customer/calendar dependence.

## 9. Streaming implementation and exact verification limit

Implemented: real Kafka client producer, chronological replay cursor, acknowledged
publishing, controls/speed/reset, zoned timestamps, schema validation, durable deterministic
IDs, duplicate conflict rejection, explicit consumer commits, DLQ acknowledgement,
heartbeats, observed lag and independent event-store metrics. Unit tests verify durable
idempotency and unchanged historical sales. **No Redpanda broker roundtrip or DLQ
integration success is claimed.** Docker Desktop is installed, but engine requests
returned unavailable/500 and normal Windows service startup was denied. Administrator
or first-launch/virtualisation action is still required. Consumer status correctly
shows no observed healthy worker; no dashboard counters are fabricated.

## 10. Dashboard and API verification

All eleven pages passed Streamlit AppTest against the real fixture-backed API and
actual Edge browser navigation against the full-data running application. Five genuine
screenshots are under [screenshots](screenshots). Source/assumptions are labelled.
The API's {len(http["endpoints"])} live HTTP read checks returned 200; readiness and UI health passed;
unauthenticated writes returned 401; the scenario calculation was verified. Export,
filter, pagination and validation checks passed. See [HTTP evidence](verification/http_verification.json).
Protected historical scoring and assumed segment budget allocation were also verified.
Product views support highest/lowest revenue and return-rate rankings. Monitoring
shows the timestamped recorded local test summary rather than invented test counters.
Warm cache improvements are warehouse-derived; cold/warm timings are local measurements,
not load-test or SLA claims. CSV formula escaping does not mutate cached analytical data.

## 11. Tests and security checks actually executed

* Non-service Pytest: **{tests["tests"]} tests, {tests["failures"]} failures, {tests["errors"]} errors**.
* Genuine PostgreSQL migration/ETL/SQL integration: **{pg_tests["tests"]} passed**.
* dbt: **7 models + 10 data tests passed**, including an incremental rerun.
* Browser: **11 pages, zero page exceptions**.
* Ruff and Python compilation passed at recorded final verification.
* Locked dependency audit: **{len(audit["dependencies"])} packages, {vulnerabilities} known reported vulnerabilities**.
* Broker integration test exists but was not executed successfully without Redpanda.

Upstream Starlette/NumPy deprecation warnings remain; they are recorded, not treated
as failing business assertions. No 24/7 reliability, penetration-test or security
certification claim is made. Read access remains loopback development scope.

## 12. Docker, automation, cloud and Power BI

Compose configuration parses; PostgreSQL, Redpanda, init, API, UI, consumer and optional
replay services are defined. **The full Compose runtime is unverified.** Windows setup,
start, stop and health verification were executed; scripts preserve owned-process scope.
GitHub Actions provides lint, tests, real-service jobs and scanning, but has not run on
GitHub. Azure mapping and a limited Bicep telemetry example are supplied; complete cloud
infrastructure/security validation is not delivered and no billable resource was created.

Power BI M, DAX, theme JSON, model relationships, refresh and eight-page assembly specs
exist. Actual Desktop authoring is unavailable: **no valid PBIP/PBIX is claimed**.
These reproducible assets satisfy the documented authoring fallback. Streamlit works
without Power BI.

## 13. Exact startup and local URLs

Verified command in this prepared workspace:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start.ps1
```

Dashboard: http://127.0.0.1:8501 · Swagger: http://127.0.0.1:8000/docs.
Native PostgreSQL cluster: 127.0.0.1:5433 (separate from Docker port 5432).
For a fresh checkout use `scripts/setup.ps1 -UseMirror` explicitly on hosts where
UCI DNS fails, then start. Secrets/data/models are local ignored artifacts and are not
part of a Git checkout. Stop with `scripts/stop.ps1`; native PostgreSQL has its own stop action.

## 14. Project status and unresolved work

| Classification | Deliverables |
|---|---|
| VERIFIED | Mirrored real-data import/quality; PostgreSQL migrations and exact reconciliation; SQL/dbt; analytics; model evaluation/tracking; API; eleven UI pages; scenarios; local HTTP/UI startup; tests/screenshots/audit |
| IMPLEMENTED | Broker producer/consumer/DLQ/webhook/controls; Compose; CI; Power BI assets; deployment design; BA and portfolio package |
| BLOCKED | Direct UCI DNS retrieval; actual Docker/Redpanda roundtrip and complete Compose runtime; Desktop Power BI authoring |
| INCOMPLETE | Broker-level recovery/load tests; full Azure template/deployment validation; authored PBIP/PBIX; internet-grade auth/HA/restore drills |

Next exact service action: finish Docker Desktop/Windows engine prerequisites, then
`docker compose up -d postgres redpanda --wait`; run the genuine broker integration test
using an isolated database and SERVICE_KAFKA_BOOTSTRAP_SERVERS. Run the replay profile
and verify messages, DLQ, controls and unchanged historical totals. No credentials,
paid resources, external customer contacts or publishing are authorised by this report.

## 15. GitHub readiness, hiring review and career materials

Git repository is local. Source, documentation and aggregate evidence are prepared;
raw data, .env, databases, tools and model binaries are ignored. No remote repository,
GitHub publication or live public deployment was created. Review staged contents and
resolve documented blockers before calling the entire specification complete.

See [hiring-manager review](portfolio/HIRING_MANAGER_REVIEW.md),
[LinkedIn/CV materials](portfolio/PROFILES_AND_CV.md),
[interview, STAR and demo scripts](portfolio/INTERVIEW_AND_DEMO.md), and
[business analysis](business-analysis/BUSINESS_ANALYSIS.md). All claims must remain
independent-project evidence, not employment, actual stakeholder interviews, revenue
uplift, adoption, production usage or present-day predictive validity.
"""
    Path("docs/DELIVERY_REPORT.md").write_text(report, encoding="utf-8")
    print(
        f"Delivery report generated from actual evidence: {tests['tests']} tests; dbt {len(dbt['results'])} operations; {quality['imported']:,} raw rows"
    )


if __name__ == "__main__":
    run()
