# Truthful LinkedIn, GitHub and UK CV materials

These describe an independent portfolio project, not employment. Consult the delivery
report for actual execution and measurements before publishing any claim. Coding-agent
assistance was used; the owner must be able to explain and reproduce the evidence.

## LinkedIn project description

UK Commerce 360° connects auditable historical-data ingestion, SQL modelling, customer
analytics, predictive evaluation, FastAPI and an eleven-page Streamlit application.
Using UCI Online Retail II (2009–2011), it demonstrates revenue reconciliation,
RFM/cohort analysis, product associations and explicitly hypothetical marketing scenarios.
PostgreSQL/dbt and Redpanda assets accompany automated tests and Windows automation.
The delivery report distinguishes implemented components from verified service execution.

## LinkedIn technical case study

The project asks how an analyst could trust fragmented commerce reporting and turn
historical transactions into defensible decisions. The pipeline preserves source rows,
records accepted/quarantined/duplicate dispositions, uses decimal amounts and retains
unidentified buyers in revenue. Customer-facing outputs use pseudonymous identifiers.

Customer analysis combines RFM segments, purchasing timelines and monthly cohorts.
Repurchase evaluation uses chronological cutoffs, future labels and horizon separation.
Daily forecasting compares naive, seasonal-naive, statistical and regularised lag models
with rolling origins. Actual model scores and limitations are saved rather than assumed.
The streaming implementation uses a real Kafka-compatible producer/consumer and a separate
event store so replay cannot double-count historical sales.

This is an independent learning and engineering exercise. Campaign spend, attribution
and observed costs are absent; no commercial uplift, clients, adoption or production
deployment is claimed. See the repository's execution report for evidence and blockers.

## LinkedIn launch post

I built UK Commerce 360°, an independent portfolio project exploring transparent,
reproducible historical retail intelligence.

It brings together Python pipelines, SQL modelling, customer cohorts, RFM segmentation,
chronological machine-learning evaluation, forecasting, APIs and a Streamlit application.
A separate streaming implementation replays historical transactions without presenting
them as current commerce activity or inflating historical revenue.

The most useful lesson: data quality, target leakage and KPI definitions belong in the
product requirements. The repository includes actual test/model evidence, business
analysis, reporting assets and clear limitations. Source: UCI Online Retail II, 2009–2011,
CC BY 4.0. Built with coding-agent assistance.

Repository/demo link: **[Add only after authorised publication.]**

## GitHub repository summary

Historical UK commerce intelligence: auditable Python ETL, SQL star schema/dbt assets,
RFM/cohorts, repurchase and forecast evaluation, FastAPI, Streamlit and Redpanda replay
implementation. Independent portfolio; actual verification and limitations documented.

## UK Data Analyst CV bullets

* Built historical sales analysis with documented gross, returns, net, AOV and repeat-rate
  definitions supported by automated calculation tests.
* Analysed customer cohorts, value segments, country demand and product returns using
  interactive filters and management-report exports.

## UK Business Analyst CV bullets

* Produced a business case, hypothetical stakeholder personas, requirements, user stories,
  acceptance criteria, process diagrams and a requirements-to-evidence matrix.
* Defined a transparent cost-benefit scenario framework separating assumed campaign
  contribution from observed sales; documented governance and delivery risks.

## UK BI Analyst / Power BI Developer CV bullets

* Designed a retail star schema and reproducible Power Query, DAX, theme and relationship
  specifications for an eight-page Power BI report.
* Implemented an eleven-page Streamlit application for sales, customer, product and
  operational intelligence. Qualify Power BI Desktop assembly separately in interviews.

## UK Marketing Analyst CV bullets

* Used customer value, recency and frequency to formulate testable retention and targeting
  hypotheses without claiming measured campaign uplift.
* Built audience, response, incrementality and contribution sensitivity scenarios with
  explicit assumptions and break-even calculations.

## UK Data Scientist CV bullets

* Implemented 30-day repeat-purchase evaluation with chronological snapshots, horizon
  separation, future labels, baseline comparisons and calibration diagnostics.
* Compared daily revenue forecasting methods using rolling origins and a held-out final
  horizon; documented uncertainty assumptions and historical-data limitations.

## UK Data Engineer CV bullets

* Developed checksum-based, chunked ingestion with raw lineage, quarantine, Decimal money,
  source reconciliation and idempotent retry behaviour.
* Created PostgreSQL migrations, dbt models, container orchestration and Kafka-compatible
  producer/consumer code with durable duplicate protection. Describe actual service
  execution only as verified if the delivery report supports it.

## UK Machine Learning Engineer CV bullets

* Built reproducible scikit-learn training, saved inference artifacts, MLflow tracking,
  model execution history and API delivery of historically scored probabilities.
* Added temporal leakage tests, baseline evaluation and monitoring design; preserved
  frozen evaluation artifacts separately from refitted serving artifacts.

Measured figures may only be added from docs/DELIVERY_REPORT.md. Never invent financial
impact, model scores, performance improvements, employment or production adoption.
