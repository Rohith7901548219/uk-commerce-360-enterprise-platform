# GitHub publication verification report

Prepared 16 November 2026 (Asia/Kolkata). **Public publication approved; upload pending.**
Target: Rohith7901548219/uk-commerce-360-enterprise-platform. The owner explicitly
approved this security review and public publication after reviewing the prepared
package. Repository creation, commit/push and remote verification are authorized.

## Owner review: approved for public publication

The approved review covers **151 publication candidate files** and the original
**one commit / 130 historical blobs**. No credential signatures, exact known local
secret values, prohibited data paths or broken local Markdown links were detected.
See the timestamped [security scan](verification/publication-security.json).

The proposed publication includes application source, SQL/dbt/Alembic definitions,
tests, locked dependencies, infrastructure examples, documentation, five reviewed
screenshots, aggregate historical results and the nine-row synthetic test fixture.
Environment files, raw/source datasets, local databases, trained model binaries,
installed runtimes and private keys stay excluded and remain on this computer.

The scoped scanner does not guarantee detection of every possible secret; images
were reviewed manually during the earlier preparation. The functional limitations
below remain part of the review. Authentication does not approve publication.
**Visibility approval: public. Security-review approval: granted on 16 November 2026.**

The owner explicitly selected Rohith7901548219 as the destination after the browser
login identified that account. GitHub API account verification succeeded. A read-only
lookup of the target repository returned HTTP 404; no repository was created.

## Scope and source inventory

Existing commit 0cedb0136ff4f9667691c81045001005ad2c9cf3 is preserved. The project
contains a modular Python package for acquisition/ETL, SQLAlchemy warehouse, analytics,
ML, API and streaming; SQL/Alembic/dbt assets; eleven Streamlit pages; Power BI source
assets; Docker/Windows/CI automation; tests, real screenshots and portfolio documentation.
No empty folders or superficial duplicated source trees were created.

## Checks completed in this publication preparation

| Check | Actual result |
|---|---|
| Git inventory / baseline | One existing commit; no remote initially configured |
| Ruff | PASS after publication tooling changes |
| Non-service Pytest | 54 passed, 2 service tests deselected; 13 upstream deprecation warnings |
| Security guard regression | Removed historical fake credential still blocks publication; ignored local config remains on disk |
| Working publication candidates | Refreshed scan: 151 candidates; no credential signatures, exact known local credentials or prohibited data paths detected |
| Reachable Git history | One commit / 130 blobs scanned; no historical credential or private/generated-path findings |
| Reviewed sample exception | Only data/fixtures/retail.csv: nine synthetic rows, SHA256 5f3e3c9d689d368c4817e314ded28235d002cc8fb92832fb94af5b7eaa752556 |
| Documentation links | Refreshed publication scan found no broken local links |
| Existing screenshots | Capture timing corrected; all 11 completed pages checked and five genuine screenshots recaptured and manually reviewed |
| Trusted ML artifact re-inference | PASS: all 3,477 stored scores matched recomputation; maximum absolute difference 4.9997e-09; feature cutoffs and model-run identity checked |
| Actual PostgreSQL/SQL | PASS: migration/fixture integration and all analytical SQL; full raw/staging/fact reconciliation; fact/mart net sales GBP 19,013,462.68 |
| Live API/UI | PASS: 17 read endpoints, authenticated historical scoring, rejected unauthenticated writes, hypothetical scenarios/allocation, and Streamlit health |
| Locked dependency advisory scan | 145 packages scanned; no known reported vulnerabilities |
| Docker Compose | Configuration validation exit 0; complete container/broker runtime remains unverified |
| Python compilation | PASS for source, app, scripts and tests |
| Isolated publication copy | PASS: all 54 tests and the security audit passed without .env, raw data, model binaries or private credential environment variables; existing installed dependencies were reused |
| GitHub CLI | Official checksum-verified portable CLI; official browser authorization completed |
| Authentication / target remote | Verified as owner-approved Rohith7901548219; target repository lookup returned HTTP 404; no repository created, remote configured or project files uploaded |
| GitHub-hosted CI | Not run yet; no published remote commit exists |

New execution evidence is stored as publication-* artifacts under
[verification](verification), including [tests](verification/publication-tests.xml),
[ML](verification/publication-ml.json), [API](verification/publication-http.json),
[browser](verification/publication-browser.json), [PostgreSQL](verification/publication-postgres.json),
[dependency audit](verification/publication-dependency-audit.json) and
[Compose configuration](verification/publication-docker.json).
The [clean-copy check](verification/publication-clean-checkout.json) validates ordinary
CI inputs independently of this prepared workspace's private files. Its Windows-only
read-only Git-object cleanup issue was fixed; the complete rerun exited successfully.
The original full-data evidence remains in [DELIVERY_REPORT.md](DELIVERY_REPORT.md)
and [verification artifacts](verification). Historical results are not relabelled as
new test runs.

## Data and security handling

.gitignore excludes environment variants, local tools/venvs, caches, logs, databases,
model binaries, raw/private/downloaded data, Excel/CSV/Parquet files and key material.
The sole CSV exception is the intentionally reviewed synthetic fixture. Excluded
files are retained on the owner's computer. The full UCI workbook is not published;
official acquisition and an explicitly opted-in, checksum-checked mirror are supported.

Checks cover all current publication candidates and reachable historical Git blobs,
known credential signatures, exact local secret values and risky paths. Local private
data are inventoried; installed third-party runtimes are excluded from project-source
inspection. Images are manually reviewed separately. This is a scoped security review,
not a guarantee of detecting every possible secret or a penetration-test certification.
If an actual historical secret is discovered, publication must stop for owner review.

## Known functional limitations

* Actual Redpanda/Docker Compose runtime was not verified in the original environment.
  Historical replay/DLQ code is implemented; it is not genuine current retail activity.
* Direct UCI download was blocked by host DNS; the local real-data run used an explicitly
  attributed mirror whose checksum matches published mirror metadata.
* Power BI M/DAX/calendar/theme/model/page assets exist; no authored PBIP/PBIX is claimed.
* Azure mapping and a limited Bicep example exist; complete cloud deployment/security
  validation and billable deployment have not been performed.
* The application uses loopback development access, not internet-grade authentication/HA.
* Repurchase threshold recall is low; selected forecasting lost to seasonal-naive on the
  final test. No causal ROI, profit, uplift, customers or employment experience is claimed.

## Publication gate

Only publish after explicit owner approval of both this security review and repository
visibility, completed authentication as Rohith7901548219, and safe inspection/preservation
of any existing remote work. Never force-push. Verify the remote SHA equals local HEAD
and inspect the actual GitHub Actions run after an approved push. A private-repository
choice requires an explicit owner response too. No publication is implied by browser login.

Official browser authorization is complete and the GitHub API confirms the active
account is Rohith7901548219, now explicitly selected by the owner. The abandoned
login flow for the earlier target was stopped. No device code, token or private
authentication file is part of the publication set. No GitHub password or personal
access token was requested in chat.
