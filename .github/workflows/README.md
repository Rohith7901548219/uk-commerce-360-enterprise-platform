# CI scope

Every push and pull request runs a locked Python environment, Ruff, fixture-based
unit/API/SQL/ML-feature/Streamlit tests, publication/history checks and a dependency
advisory scan. No UCI download, model binaries, private environment file, paid service
or user-supplied repository secret is required for these ordinary checks.

The PostgreSQL/Redpanda job is explicitly opt-in using workflow_dispatch and the
run_services input. It creates local disposable CI services and random local secrets.
The presence of this job is not evidence that a broker integration has passed. See
the actual run results and docs/verification-report.md. No cloud deployment occurs.
