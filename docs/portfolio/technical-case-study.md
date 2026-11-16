# Technical case study

## Business problem and scope

A hypothetical UK retailer needs consistent revenue/returns reporting, clearer
customer behaviour and defensible forecasting. This independent portfolio uses real
historical UCI transactions, not live current commerce or an actual client engagement.

## Architecture decisions

Preserve source rows before transformation. A checksum/sheet/row identity supports
lineage and retry; business fingerprints identify exact duplicates. Accepted sales and
returns enter separate Decimal-based facts with customer/product/date/country dimensions.
Missing customer IDs remain in valid sales totals but are excluded from customer models.
HMAC customer keys protect application outputs without pretending the data is anonymous.

SQLAlchemy and Alembic support PostgreSQL plus a labelled SQLite development/test mode.
dbt manages repeatable analytical marts. FastAPI provides validated services, and an
eleven-page Streamlit application uses backend computations. A separate event store
prevents historical replay from inflating warehouse revenue. Redpanda/Kafka-compatible
code requires actual broker verification before operational reliability is claimed.

## Validated historical outcomes

The source contains 1,067,371 imported lines: 1,027,017 accepted, 34,335 duplicates and
6,019 quarantined under the documented rules. PostgreSQL facts and the daily dbt mart
reconcile to GBP 19,013,462.68 net sales. These are historical calculations, not claimed
commercial impact. Seven dbt models and ten tests passed in the prior full-data run.

Repeat-purchase features precede their cutoffs and labels use the following 30 days.
The validation-selected Random Forest achieved test average precision 0.6474 against
prevalence 0.3882; recall at threshold 0.5 was 18.3%. The final-test logistic-regression
AP was higher, but the held-out test was not used for selection. Forecast selection used
development MAE: Holt-Winters later produced WAPE 26.28%, versus seasonal-naive 22.77%.
These results demonstrate comparison and honest limitations rather than universal superiority.

## Deployment and recommendations

Local Windows automation and a native PostgreSQL runtime were exercised. Compose,
optional service CI and Azure design assets are provided; full container/cloud runtime
is not claimed. Data/model binaries and secrets stay local and are rebuilt using scripts.

Investigate quality exceptions first, then use RFM and propensity rankings to formulate
authorised experiments. Validate calibration and decision thresholds before action.
Campaign spending, attribution, unit costs and profit are absent: hypothetical scenarios
cannot establish causal marketing ROI. Prioritise broker testing, restore exercises,
Power BI authoring and catalogue governance before stronger operational claims.

See [current publication verification](../verification-report.md) and the
[original detailed delivery evidence](../DELIVERY_REPORT.md). Stakeholders are personas,
not interviewed people; the work was completed with coding-agent assistance.
