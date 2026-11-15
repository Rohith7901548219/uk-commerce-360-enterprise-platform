# Interview and demonstration materials

## Technical interview questions

1. Why is invoice-line grain different from order grain for AOV and frequency?
2. How do source checksum, raw row key and business fingerprint differ?
3. Why retain unidentified sales while excluding them from customer models?
4. How is a cancellation with positive source quantity interpreted?
5. How does the label-horizon embargo reduce temporal leakage?
6. Why can known customers occur across chronological splits?
7. Why compare average precision with prevalence rather than accuracy alone?
8. How does calibration differ from ranking quality?
9. Why is the forecast uncertainty band approximate?
10. What happens if a consumer crashes between database and broker commits?
11. Why does replay not change historical sales totals?
12. What happens if DLQ delivery fails?
13. When does a dbt backfill require full refresh?
14. What do actual query plans show about the customer/time indexes?
15. What security and reliability work remains before public deployment?

## Business interview questions

1. Which decision does each executive KPI support?
2. Why can this source not establish marketing ROI or observed profit?
3. What would real stakeholders need to validate about RFM definitions?
4. How would you prioritise missing customer IDs versus returns exceptions?
5. What experiment would validate a retention hypothesis?
6. How would you communicate a model that loses to seasonal-naive?
7. What additional data supports stockout-aware demand forecasting?
8. Which acceptance criteria are required before production adoption?

## STAR narrative

**Situation:** a hypothetical retailer faced fragmented historical reporting. This was
a portfolio scenario, not employment or client work.

**Task:** build reproducible intelligence that reconciles transactions and evaluates
customer/forecast signals without invented business impact.

**Action:** implemented auditable validation, decimal monetary rules, schema/SQL assets,
analytical services, dashboards and temporal evaluation. Tested calculations and recorded
environment limitations. Used coding-agent assistance and reviewed evidence before use.

**Result:** reference the delivery report's actual imported counts, test outcomes and
model metrics. Explain unresolved service/Power BI constraints. No assumed savings or
customer retention uplift is substituted for measured outcomes.

## Five-minute demonstration

1. Show the historical banner, provenance and quality reconciliation.
2. Explain gross/returns/net and reproduce a KPI using SQL/API.
3. Filter a market, inspect product returns and explain period limitations.
4. Inspect a pseudonymous customer, RFM segment and cohort heatmap.
5. Compare repurchase candidates, calibration and cutoff/label windows.
6. Show forecast baselines, held-out results and uncertainty assumptions.
7. Change a hypothetical scenario response rate; make no ROI claim.
8. If broker services actually run, publish replay messages and verify durable events
   with historical revenue unchanged. Otherwise show the explicit verification blocker.
9. Show tests, architecture, Power BI assets and known limitations.

## Two-minute video narration

“UK Commerce 360 is my independent portfolio project for historical retail intelligence.
It uses UCI Online Retail II, covering 2009 to 2011, rather than current live sales.

The executive page brings gross sales, returns and net sales into one reconciled view.
The pipeline preserves source records and flags invalid rows and duplicates. Valid
unidentified sales remain in revenue, while customer outputs use pseudonyms.

Customer 360 explores RFM and cohort retention. Product intelligence examines sales and
returns. Marketing scenarios use assumptions because campaign spending and causal
attribution are absent from the dataset.

Predictive features precede each historical cutoff and labels use later purchases.
Models are compared against baselines using chronological evaluation and calibration.
Forecasting uses rolling origins and a final held-out horizon.

The event-processing implementation uses a Kafka-compatible broker and separate storage
so replay cannot inflate historical sales. The delivery report states which services
actually ran and which depend on environment requirements.

The repository includes tests, business requirements, reporting assets and limitations.
This is an engineering demonstration, not a claim of commercial deployment, financial
improvement or employment experience.”

## Skills-to-project evidence matrix

| Skill | Evidence | Actual verification |
|---|---|---|
| SQL | sql/analytics, dbt/models | Query tests; service checks separately |
| Python/ETL | commerce/ingest.py, db.py | Reconciliation and retry tests |
| Customer analytics | RFM, retention, basket_rules | Automated tests and pages |
| ML | ml.py, model cards | Saved actual evaluation and run logs |
| API | api.py | Route/auth/filter/export tests |
| Streaming | streaming.py | Idempotency unit test; broker check separately |
| BI | dashboard.py, powerbi assets | App tests/screenshots; Desktop authoring separate |
| BA | Business analysis package | Requirements and acceptance traceability |
| DevOps | Compose, scripts, CI | Recorded startup/service evidence |
| Governance | Methodology and runbook | Claims traceable to evidence |
