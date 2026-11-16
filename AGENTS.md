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
Record unresolved dependencies and exact next actions. No cloud creation is authorised.
The owner selected Rohith7901548219/uk-commerce-360-enterprise-platform as the
publication target on 16 November 2026, replacing the earlier rohithmuskem target.
GitHub CLI account identity has been verified as Rohith7901548219.
Public visibility requires the owner's explicit confirmation
after the reviewed source/security/verification package is ready. Preserve remote
history, never force-push, and stop publication if historical secrets are detected.
Use official browser/device login; never request passwords or tokens in chat.
On 16 November 2026 the owner explicitly approved the security review and public
publication to the selected target. This authorizes committing and publishing the
reviewed project, then verifying the remote commit, README and GitHub Actions.
Preserve that approval; do not request it again for the same reviewed scope.
Docker Desktop installation has been authorized
by the owner in this session. Do not run destructive resets without explicit scope.

Local Git is installed at C:/Program Files/Git/cmd/git.exe. Its metadata ownership
was assigned to the owner's Windows account after sandbox ownership caused Git to
refuse access. The permission profile may require escalation for .git mutations.
Use the installed workspace uv/Python when PATH lacks them. The application is
already initialized with real, explicitly labelled mirror data and trained artifacts.

Publication preparation must keep all local raw data, model binaries, databases and
secrets on disk but outside Git. The sole CSV exception is the reviewed nine-row
synthetic fixture data/fixtures/retail.csv. Use scripts/audit_publication.py to check
the working publication set and all reachable Git history before any push.
