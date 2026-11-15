# Source, warehouse and lineage dictionary

Source: Chen, D. (2012), Online Retail II, [UCI](https://archive.ics.uci.edu/dataset/502/online+retail+ii),
[DOI](https://doi.org/10.24432/C5CG6D), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Official description: historical UK retailer, 1 December 2009–9 December 2011.
Actual imported statistics are generated in docs/DELIVERY_REPORT.md.

| Source field / aliases | Curated field | Rule |
|---|---|---|
| Invoice / InvoiceNo | invoice | String; C prefix interpreted as cancellation |
| StockCode | stock_code | Non-empty bounded alphanumeric code; heuristic category |
| Description | dim_product.description | First encountered description; missing labelled Unknown product |
| Quantity | quantity | Finite nonzero integer; cancellation quantities made negative |
| InvoiceDate | event_time / date_key | Europe/London source assumption → UTC timestamp; local business date retained |
| Price / UnitPrice | unit_price | Decimal(18,4), strictly positive; zero/negative invalid |
| Customer ID / CustomerID | customer_key | Stable 24-character HMAC-SHA256 prefix; missing stays NULL |
| Country | country | Residence text; missing becomes Unknown with issue flag |
| Derived | amount | quantity × unit_price, Decimal(18,2), ROUND_HALF_UP |

Raw ID = SHA256(source file checksum : sheet : physical row number). Fingerprint =
SHA256 of canonical source business values including description. Exact duplicates
across chunks/sheets are retained in raw/staging and excluded from facts. This policy
cannot distinguish a legitimate identical second line from accidental duplication;
the original rows remain available for alternative policies.

| Table | Grain / key | Purpose |
|---|---|---|
| source_files | Workbook SHA256 | Provenance, fixture/mirror flag and completion |
| raw_retail_transactions | Source/sheet/row; raw_id | Unmodified serialised source payload and ingestion timestamp |
| stg_retail_transactions | raw_id | Fingerprint, accepted/quarantined/duplicate disposition and issue list |
| dim_customer | customer_key | Identified pseudonymous customer |
| dim_product | stock_code | Description and heuristic merchandise category |
| dim_country | country | Source residence label |
| dim_date | observed business date | Year/month/weekday; Power BI must extend to continuous dates |
| fact_sales_transactions | Accepted positive source line | Amount/quantity and dimension foreign keys |
| fact_returns | Accepted negative/cancelled source line | Negative amount/quantity and foreign keys |
| fact_customer_activity | customer + invoice | Positive purchase order value/time/product diversity |
| analytics.mart_daily_sales | Local business date | dbt incremental gross/returns/net/order measures |
| analytics.mart_monthly_sales | Month | Revenue aggregates |
| analytics.mart_customer_rfm | Customer | RFM measures and segments |
| analytics.mart_customer_cohorts / retention | Cohort + month offset | Observed cohort counts and rates |
| analytics.mart_product_performance | Product | Revenue rank, sold/returned units |
| mart_customer_predictions | Customer at latest training as-of | Probability and model run lineage |
| mart_revenue_forecasts | Forecast date | Historical future net-sales prediction and residual band |
| stream_events | Deterministic event ID | Independent processing history; never added to sales facts |
| stream_runtime | State key | Worker heartbeats, control state, cursor and observed lag |
| pipeline_execution_logs | Run UUID | Start/end, success/failure and reconciliation |
| data_quality_results | Run UUID + metric | Import dispositions and overlapping issue counts |
| model_execution_logs | Run UUID | Training time, actual metrics and artifact path |

Descriptions can vary for a product; first encountered value is a simplifying SCD-1
policy, not a verified canonical catalogue. Raw payloads preserve the alternatives.
Source invoice timestamps lack an explicit zone: Europe/London is an assumption.
Ambiguous or nonexistent local times should be quarantined for review. Replay time
is UTC publishing time; ingestion time is UTC durable consumer processing time.
