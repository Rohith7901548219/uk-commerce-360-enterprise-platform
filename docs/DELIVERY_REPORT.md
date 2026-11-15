# Delivery and verification report

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
is 2009-12-01 to 2011-12-09. All **1,067,371** lines remain
in raw/staging. The actual workbook was acquired from an explicitly attributed public
mirror because this host could not resolve UCI, even outside the sandbox.

SHA256: `bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980`.
It matches the mirror's published metadata. Direct UCI byte verification remains pending.
See [acquisition script](../scripts/acquire_mirror.py). Original attribution: Chen, D.
(2012), Online Retail II, UCI, DOI 10.24432/C5CG6D, CC BY 4.0. The application labels
mirror provenance and historical dates. No full dataset or raw customer IDs are tracked.

## 4. Data quality and reconciliation

| Metric | Actual records |
| --- | --- |
| imported | 1,067,371 |
| accepted | 1,027,017 |
| non_merchandise_code | 6,093 |
| cancellation | 19,494 |
| return | 22,951 |
| quarantined | 6,019 |
| invalid_price | 6,207 |
| missing_customer | 243,007 |
| duplicate | 34,335 |
| missing_description | 4,382 |
| reconciled | 1 |

Accepted + quarantined + duplicate = imported exactly. Accepted facts consist of
**1,007,913 sales lines and 19,104 return lines**. Issue counts overlap dispositions:
for example invalid-price warnings include duplicate rows, so they must not be summed
as exclusive rejected counts. Missing customer IDs remain in valid revenue; returns
are negative and customer outputs are keyed HMAC pseudonyms. Raw lineage is retained.

PostgreSQL fact net revenue and dbt daily mart both equal **£19,013,462.68**.
Actual full table counts and EXPLAIN ANALYZE output are in
[PostgreSQL verification](verification/postgres_verification.json).

## 5. Actual business metrics

| KPI | Actual historical result |
| --- | --- |
| Gross sales | £20,476,260.43 |
| Returns | £1,462,797.75 |
| Net sales | £19,013,462.68 |
| Positive-purchase orders | 40,077 |
| Identifiable positive-purchase customers | 5,878 |
| Gross average order value | £510.92 |
| Within-period repeat-purchase rate | 72.39% |

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
performance. Selection: **random_forest**. Test sample: **3,246** customers;
positive prevalence **38.82%**. Average precision is reported as
AP/PR-AUC, not trapezoidal integration.

| Candidate | Test AP / PR-AUC | ROC-AUC | Precision | Recall | F1 | Brier |
| --- | --- | --- | --- | --- | --- | --- |
| prior_baseline | 0.3882 | 0.5000 | 0.0000 | 0.0000 | 0.0000 | 0.2594 |
| logistic_regression | 0.6583 | 0.7189 | 0.8644 | 0.1619 | 0.2727 | 0.2204 |
| random_forest | 0.6474 | 0.7074 | 0.8431 | 0.1833 | 0.3012 | 0.2221 |
| gradient_boosting | 0.6481 | 0.7117 | 0.7828 | 0.2317 | 0.3576 | 0.2187 |

At threshold 0.5, recall is only 18.3%; calibration and threshold costs
need business review. No retention uplift or causal usefulness is established. Customers
can recur across time splits because the objective concerns existing buyers. Final-day
incompleteness/right-censoring is documented. Frozen evaluated and refitted serving
artifacts are separate; actual reports, parameters, versions and source checksum are saved.
Training was executed twice with the same selected models and measured headline metrics.

## 8. Forecasting, segmentation and statistical analysis

Daily net sales; three development origins select by MAE and the final 28-day horizon
is held out. Selection: **holt_winters**.

| Candidate | Development MAE | Final test MAE | Final test RMSE | Final test WAPE |
| --- | --- | --- | --- | --- |
| naive | £16,438.85 | £19,973.43 | £27,451.77 | 41.79% |
| seasonal_naive | £14,357.15 | £10,880.10 | £14,453.91 | 22.77% |
| holt_winters | £10,335.18 | £12,561.39 | £16,715.29 | 26.28% |
| ridge_autoregression | £12,163.05 | £14,364.22 | £19,211.28 | 30.06% |

Approximate 90% residual bands are not guaranteed coverage. Forecast dates follow the
historical source end, not today. RFM segmentation, 30-day membership stability and
temporal basket-rule summaries are saved. The seeded invoice bootstrap gives a 95%
mean-AOV interval of £497.64–£526.41;
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
The API's 17 live HTTP read checks returned 200; readiness and UI health passed;
unauthenticated writes returned 401; the scenario calculation was verified. Export,
filter, pagination and validation checks passed. See [HTTP evidence](verification/http_verification.json).
Protected historical scoring and assumed segment budget allocation were also verified.
Product views support highest/lowest revenue and return-rate rankings. Monitoring
shows the timestamped recorded local test summary rather than invented test counters.
Warm cache improvements are warehouse-derived; cold/warm timings are local measurements,
not load-test or SLA claims. CSV formula escaping does not mutate cached analytical data.

## 11. Tests and security checks actually executed

* Non-service Pytest: **52 tests, 0 failures, 0 errors**.
* Genuine PostgreSQL migration/ETL/SQL integration: **1 passed**.
* dbt: **7 models + 10 data tests passed**, including an incremental rerun.
* Browser: **11 pages, zero page exceptions**.
* Ruff and Python compilation passed at recorded final verification.
* Locked dependency audit: **145 packages, 0 known reported vulnerabilities**.
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
