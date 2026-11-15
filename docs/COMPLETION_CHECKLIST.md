# Definition-of-done audit

15 November 2026. **FULL PROJECT COMPLETION: NOT ACHIEVED.** All feasible local core
components are implemented and tested; the outstanding service/authoring items remain
explicit. Read the delivery report for measured evidence.

- [x] Real historical workbook acquired from an explicitly attributed mirror; mirror checksum verified.
- [ ] Direct official UCI acquisition and byte comparison (host DNS blocked).
- [x] Auditable data quality pipeline executes on 1,067,371 rows.
- [x] Real PostgreSQL schema/migrations and ingestion integration execute.
- [x] Raw, staging, dispositions and sales/return facts reconcile.
- [x] dbt transformations execute; full and incremental runs pass.
- [x] Advanced SQL analytics execute in actual PostgreSQL.
- [x] RFM/customer segmentation, cohorts and product associations work.
- [x] Repeat-purchase model evaluated chronologically with baselines.
- [x] Forecast models evaluated with rolling origins and final holdout.
- [x] Repeated seeded training produces the same selected models and headline metrics.
- [x] MLflow experiment/run records and saved artifacts exist.
- [x] FastAPI starts; live health and readiness return 200.
- [x] API integration/validation/auth/filter/export tests pass.
- [x] Streamlit starts and reads processed backend data.
- [x] All eleven pages pass AppTest and real browser navigation.
- [ ] Redpanda broker runs and passes health verification.
- [ ] Replay producer publishes to an actual running broker in this environment.
- [ ] Consumer broker roundtrip, DLQ, offset/restart and controls verified.
- [x] Durable event idempotency/conflict rejection tested against the database in unit tests.
- [ ] Live monitor demonstrated with real broker-processed events (currently correctly unavailable).
- [x] Replay/event store is isolated from historical facts in calculation tests.
- [x] Scenario simulator computes explicit hypothetical assumptions.
- [x] Data/pipeline/model monitoring reads actual stored history.
- [x] Power BI M, DAX, theme, relationships, page specs and assembly guide exist.
- [ ] Actual authored/validated PBIP or PBIX (Desktop authoring unavailable).
- [x] Compose configuration parses and Docker Desktop was installed with authorisation.
- [ ] Full Docker Compose deployment runs successfully.
- [x] Non-service test suite, genuine PostgreSQL test, dbt tests and lint pass.
- [x] Locked dependency scan executed; no known reported vulnerabilities in scanned set.
- [x] GitHub Actions source exists.
- [ ] GitHub-hosted CI run (no remote publication performed).
- [x] BA, architecture, dictionary, model cards and operational documentation exist.
- [x] Genuine dashboard screenshots and aggregate verification artifacts exist.
- [x] LinkedIn, UK CV, interview, STAR and demonstration materials exist.
- [x] Local Git repository is prepared; generated data/secrets/tools remain ignored.
- [ ] GitHub publishing (requires explicit external publishing authorisation).
- [x] Azure architecture mapping and limited template example exist; no resource created.
- [ ] Complete Azure infrastructure validation/deployment and production security review.
- [x] Known limitations and exact next actions are documented.
