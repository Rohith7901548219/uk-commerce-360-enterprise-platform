# Local operations and recovery

Windows setup: `powershell -ExecutionPolicy Bypass -File scripts/setup.ps1`.
Local API/UI: `powershell -ExecutionPolicy Bypass -File scripts/start.ps1`.
Full services: `powershell -ExecutionPolicy Bypass -File scripts/start.ps1 -Docker`.
Stop: `scripts/stop.ps1` (or `-Docker`). Tests: `scripts/verify.ps1`.
Scripts generate secrets locally and do not print them. `.env` is ignored.

Fresh local mode defaults to SQLite. This prepared workspace uses its own native
PostgreSQL cluster on 5433, managed by start/stop.ps1. Compose overrides the URL with
its separate PostgreSQL service; this
does not migrate SQLite data automatically. Its init job rebuilds from source, then
dbt and models. API/UI bind loopback. No read authentication is provided for internet
hosting; do not expose these ports publicly without a gateway and identity layer.

Troubleshooting:

* UCI DNS/download failure: direct acquisition fails visibly. An explicitly labelled
  mirror may be used with a recorded URL and checksum; direct UCI verification remains
  separate. Never rename fixtures as real data. Use `commerce pipeline --fixture` only
  in an isolated database, otherwise the application correctly flags mixed provenance.
* Partial import: rerun the same checksum/path. Completed chunks and raw keys are
  retained; the loader skips existing rows. Failed runs are preserved in execution logs.
* PostgreSQL unavailable: check `docker compose ps`, `logs postgres`, secrets and disk.
  Alembic: `alembic upgrade head`. A rebuild must preserve source files/HMAC key.
* dbt stale after older backfill: `dbt build --full-refresh --project-dir dbt --profiles-dir dbt`.
* Consumer failure: inspect worker logs and broker availability. Restart consumer;
  auto-commit is disabled and database commits precede source offset commits. An
  invalid event is acknowledged to DLQ before rejection and source offset are committed.
* Duplicate replay: reset rewinds cursor but retains event IDs, so counts are not inflated.
* Replay controls: `docker compose --profile replay up -d replay`; page controls set
  persisted state. There must be a running worker to honor it. Completed workers need
  restart after reset. Consumer lag is null when no fresh heartbeat is observable.
* Model training: `commerce train`; insufficient small fixtures fail clearly. Saved
  artifacts must come from this project; joblib files are executable trusted inputs.
* Docker installed but engine unavailable: complete Docker Desktop's initial setup,
  accept applicable terms and ensure supported virtualisation/WSL prerequisites. Windows
  administrator action or restart may be required. Do not claim service tests passed
  on the basis of Docker client installation alone.

Reset is explicit: `scripts/reset.ps1 -ConfirmLocalReset` removes generated local
SQLite warehouse/artifacts after stopping owned processes. It retains raw files, .env
and Docker volumes. Container volume destruction is intentionally not automated.
Back up raw workbook, its manifest, secrets and PostgreSQL using pg_dump. Restore into
an isolated database and verify reconciliation before use. No restore drill is claimed
unless recorded in the delivery report. This development platform has no 24/7 SLA.
