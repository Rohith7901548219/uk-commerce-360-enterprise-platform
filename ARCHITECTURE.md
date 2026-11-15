# UK Commerce 360 architecture

Independent portfolio application using UCI Online Retail II (2009–2011), not a
live retailer. Revenue is in GBP; profit, attribution and campaign uplift are not
observed in this source.

```mermaid
flowchart TD
 U[UCI workbook + SHA256 manifest] --> R[Immutable source + raw rows]
 R --> Q[Validation, quarantine, reconciliation]
 Q --> S[Staging + SQLAlchemy star schema]
 S --> D[dbt PostgreSQL marts]
 S --> M[Chronological ML and rolling forecasts]
 S --> A[FastAPI read services]
 M --> A
 A --> F[Streamlit: eleven business pages]
 D --> P[Power BI reproducible assets]
 S --> RP[Historical replay producer]
 RP --> K[Redpanda Kafka broker]
 W[Authenticated external webhook] --> K
 K --> C[Validated consumer + dead letter topic]
 C --> E[Independent event store + operational metrics]
 E --> A
```

Primary deployment: Compose PostgreSQL, Redpanda, initialization job, FastAPI,
Streamlit and consumer. MLflow is local experiment tracking. Local SQLite mode
runs batch analytics/API/UI without pretending broker or PostgreSQL is available.
Raw data never goes to Git. Customer HMAC keys are persistent local secrets.

Batch processing is chunked and restartable, keyed by source checksum/sheet/row.
Each row carries validation disposition. Fingerprint deduplication spans chunks.
Reprocessing a checksum is idempotent. Decimal amounts reconcile sales and returns;
valid unidentified sales remain in revenue but are excluded from customer models.
Events have deterministic IDs, separate historical event, replay and ingestion
times, and do not mutate historical fact tables.
