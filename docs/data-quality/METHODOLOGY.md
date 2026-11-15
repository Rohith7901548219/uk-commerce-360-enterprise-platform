# Data quality and reconciliation

Every row is accepted, quarantined or duplicate. Row issue counts overlap and must
not be summed as a partition. The three dispositions are mutually exclusive and
reconcile exactly to imported rows. Accepted rows reconcile to sales + return facts.
Missing customer IDs and descriptions are warnings, not revenue exclusions. Invalid
prices/quantities/dates/stock codes and missing invoices are quarantined. Foreign
countries are retained and filterable. Cancellation and return indicators are tracked.

Zero prices are excluded from revenue facts under this portfolio policy, even where
a business could interpret them as free goods. All source rows remain reviewable.
Non-merchandise codes are a format heuristic and excluded only from basket analysis,
not sales. Product identifiers with unexpected but valid characters are retained
where they satisfy the bounded validation rule; invalid ones are quarantined.

Source workbook and SHA256 manifest are immutable by convention; the loader uses
conflict-ignore for raw row keys. This is auditable local storage, not a WORM guarantee.
Chunk commits make interruption recovery safe. A resumed checksum skips existing raw
keys and rebuilds activity aggregates. New source files produce new lineage; exact
business fingerprints prevent duplicate facts across sources. Historical backfills
require dbt `--full-refresh` if older than its 31-day overlap.

Validate with `sql/validation/reconciliation.sql`, automated fixture tests and dbt
revenue reconciliation. Compare gross and returns separately before net. A data-quality
run reports source-specific dispositions; warehouse KPIs can span multiple sources.
Do not confuse repeated quality runs with additional imports.

Analytical dataframes are cached by database identity and latest successful pipeline
revision. Real-data snapshots may be stored as ignored Parquet derivatives; they
contain warehouse outputs, not substitute fixtures. Filters apply to the same immutable
cached frame, and export escaping operates on a copy. A completed new import invalidates
the cache. Recovery after manual database edits requires a successful audit/rebuild.
