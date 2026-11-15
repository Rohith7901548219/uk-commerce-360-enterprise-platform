# Working agreement

Build the requested UK Commerce 360 portfolio platform in this workspace. Read
PROGRESS.md and IMPLEMENTATION_PLAN.md before continuing. Preserve existing verified
work. Never invent production use, business uplift, model scores or test results.

Use Python 3.12, uv, SQLAlchemy, FastAPI and Streamlit. The supported primary stack
is PostgreSQL + Redpanda in Compose; SQLite is an explicitly labelled local analytics
mode, never evidence that PostgreSQL or broker integration passed. Keep all source
data, secrets, artifacts, installed tools and local state ignored by Git.

Historical source timestamps are Europe/London; store normalized UTC separately
from ingestion/replay timestamps. Money uses Decimal. Source rows remain auditable,
including rejected records and duplicates. Pseudonymize customer IDs with HMAC.
Replay events never add to historical facts. Commit broker offsets only after the
database commits, and persist deterministic event IDs for duplicate protection.

Run `uv run ruff check .` and `uv run pytest` after meaningful changes. Service
tests require actual PostgreSQL/Redpanda and may only be called verified when run.
Record unresolved dependencies and exact next actions. No cloud creation or
external publication is authorized. Docker Desktop installation has been authorized
by the owner in this session. Do not run destructive resets without explicit scope.

Local Git is installed at C:/Program Files/Git/cmd/git.exe. Its metadata ownership
was assigned to the owner's Windows account after sandbox ownership caused Git to
refuse access. The permission profile may require escalation for .git mutations.
Use the installed workspace uv/Python when PATH lacks them. The application is
already initialized with real, explicitly labelled mirror data and trained artifacts.
