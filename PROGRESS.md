# Persistent implementation record

Started 15 November 2026 (Asia/Kolkata).

| Phase | Status | Evidence / next step |
|---|---|---|
| 1 Environment / architecture | VERIFIED | Workspace Python 3.12.16 and 146 locked packages; Git and Docker Desktop installed. Portable PostgreSQL 17.12 runs on 5433. |
| 2 Acquisition / quality | VERIFIED | Explicit UCI mirror matches published SHA256; 1,067,371 raw rows. Direct UCI DNS remains BLOCKED, not silently substituted. |
| 3 Warehouse / dbt | VERIFIED | Actual PostgreSQL ingestion/SQL test passed. All raw/fact/staging counts copied and reconciled; seven dbt models and ten tests PASS. |
| 4 Analytics / SQL | VERIFIED | Actual SQL, KPI, cohort, RFM and basket tests; full-data dashboards. |
| 5 ML / forecasts | VERIFIED | Real-data chronological repurchase and rolling forecasts trained; MLflow logs and saved artifacts. RF test AP 0.6474; Holt-Winters WAPE 0.2629. |
| 6 API | VERIFIED | Route/auth/filter/pagination/export tests; live health/readiness. |
| 7 Streamlit | VERIFIED | All eleven pages pass AppTest and actual browser navigation; genuine screenshots captured. |
| 8 Streaming | BLOCKED | Real producer/consumer, DLQ, controls and idempotency implemented. No broker execution claimed; Docker engine not verified. |
| 9 Power BI | IMPLEMENTED | M/DAX/theme/model and exact assembly guide. Desktop authoring not available; no fabricated PBIX/PBIP. |
| 10 DevOps | IMPLEMENTED | Compose syntax, scripts, CI and Azure example supplied. Full Compose runtime and cloud deployment unverified. |
| 11 Validation | VERIFIED | 52 non-service tests passed; actual PostgreSQL integration passed; full and incremental dbt PASS=17; eleven live browser pages pass; HTTP reads, protected historical scoring and UI health are verified. Broker verification remains blocked. |
| 12 Documentation / portfolio | VERIFIED | BA, dictionary, model cards, README, CV/LinkedIn/interview/demo package, hiring review, completion checklist and generated delivery report/evidence exist. |

Environment restrictions: CIM hardware inspection denied; no hardware claims made.
UCI DNS failed both in and outside sandbox. Explicit mirror SHA256:
bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980.
Mirror URL/provenance is recorded by scripts/acquire_mirror.py. Direct upstream comparison
is pending. Native PostgreSQL was used to finish database/dbt verification independently.

Recovery history: duplicate issue/disposition double-count corrected and audited; CSV
NaN JSON corrected after actual PostgreSQL rejection; local tool runtime was cleanly
reinstalled after an overbroad initial lint traversal. Ruff now explicitly excludes
generated environments; all subsequent lint checks pass. Missing source rows were
never replaced with invented records.

Verified evidence: docs/DELIVERY_REPORT.md, docs/verification, docs/machine-learning/results,
docs/screenshots. Full PostgreSQL fact/mart net sales: GBP 19,013,462.68. Both initial
and incremental dbt executions passed seven models plus ten tests. Runtime and complete
locked dependency scans reported no known vulnerabilities. Analytical caching was added
after observed slow reads; refresh, filters and CSV copy isolation pass regression tests.
Windows owned process-tree restart and actual HTTP/UI checks succeeded.

The prepared workspace now uses native PostgreSQL as its active API/UI backend.
Start/stop scripts manage the owned cluster on 5433; full-data training was also
rerun against PostgreSQL. SQLite remains available for fresh setups and tests.
Product ranking includes top, bottom and return-rate views. Marketing includes an
explicitly hypothetical allocation that conserves the total in pennies. Monitoring
displays the actual timestamped local test summary.

Remaining: Docker/Redpanda require a working engine/Windows prerequisite setup; run
the genuine broker tests and full Compose stack afterwards. Direct UCI byte comparison,
Desktop Power BI authoring and complete cloud validation are still outstanding. See
docs/COMPLETION_CHECKLIST.md. No publication or billable cloud resource was created.
Do not claim FULL PROJECT COMPLETION while those checks remain unverified.
