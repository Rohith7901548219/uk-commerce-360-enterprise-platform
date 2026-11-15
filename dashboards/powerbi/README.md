# Editable Power BI reporting package

Power BI Desktop authoring is not automated by the available runtime. These are
reproducible source assets, **not a validated PBIP/PBIX**. No binary is fabricated.

1. Start PostgreSQL, run Alembic, ingest the workbook and run `dbt build`.
2. In Power BI Desktop create ServerName=`localhost:5432`, DatabaseName=`commerce`.
   Use the PostgreSQL connector and store the password in the credential manager.
3. Create `LoadTable` from queries.pq, then queries invoking it for fact_sales_transactions,
   fact_returns, dim_customer, dim_product, dim_country, dim_date, mart_customer_predictions,
   mart_revenue_forecasts and data_quality_results. Import the analytics schema marts separately.
4. Create dim_date from `calendar.pq` as a **continuous daily calendar** including forecast dates; mark
   date_key as the date table. Apply single-direction relationships in model.json.
   Keep missing customer facts unmatched/blank so total revenue remains correct.
5. Create measures from measures.dax individually. Import theme.json.
6. Assemble the eight pages below; display a historical-source banner on every page.
7. Validate gross, returns, net, orders and customer counts against `/api/v1/kpis`
   under identical date/country filters. Save as PBIP using Desktop's supported export.

| Page | Visuals / measures | Filters |
|---|---|---|
| Executive Summary | Net, gross, returns, orders, AOV, repeat rate; monthly trend | Date, country |
| Revenue Performance | Daily/28-day trend, YoY (comparable complete months only) | Date, country |
| Customer Intelligence | RFM summary, contribution Pareto, customer timeline | Segment, customer |
| Customer Retention | Cohort heatmap; unobserved cells blank | Acquisition cohort |
| Product Analytics | Revenue ranks, units, returns; association-rule export | Product, country |
| Predictive Intelligence | Historical probabilities, forecast, test metrics | Model/as-of date |
| Marketing Decision Support | Disconnected What-if parameters; explicit assumption labels | Scenario inputs |
| Data Quality Monitoring | Dispositions, quality rules, execution logs | Pipeline run |

Import refresh is manual locally. Scheduled refresh requires a configured gateway
and appropriate licences; neither is claimed or purchased. Grant reporting users
SELECT on curated tables only; exclude raw customer IDs and operational secrets.
Incremental refresh must be evaluated against historical data boundaries. Forecasts
and propensity values are historical demonstrations, not current business predictions.
