# API contract and local access

Start the application and open http://127.0.0.1:8000/docs. OpenAPI is generated from
actual request/response models. Major responses have explicit Pydantic schemas;
analytical tables are record collections. All source customer IDs are excluded.

| Method / route | Function | Access |
|---|---|---|
| GET /health, /ready | Process health / database with accepted data | Local read |
| GET /api/v1/kpis | Defined gross, returns, net, orders, AOV, repeat rate | Local read |
| GET /api/v1/sales, /sales/trends | Paginated positive lines / net time series | Local read |
| GET /api/v1/customers | RFM customers; optional timeline by pseudonymous key | Local read |
| GET /api/v1/customers/segments, /customers/retention | Segment summaries / cohorts | Local read |
| GET /api/v1/products, /products/performance, /products/associations | Product results / descriptive basket rules | Local read |
| GET /api/v1/forecasts | Historical future forecast and measured evaluation | Local read |
| GET /api/v1/predictions/repurchase | Paginated historically scored probabilities | Local read |
| POST /api/v1/predictions/repurchase | Select scored historical customers by key | Bearer token |
| POST /api/v1/scenarios | Stateless calculation using explicit assumptions | Local read/calculation |
| POST /api/v1/scenarios/allocation | Penny-conserving assumed segment budget allocation | Local read/calculation |
| GET /api/v1/stream/status, /stream/events | Actual stored events and fresh worker state | Local read |
| POST /api/v1/stream/control | Persist start/pause/stop/reset and speed | Bearer token |
| POST /api/v1/ingestion/events | Validate external event; require actual broker ack | Bearer token |
| GET /api/v1/data-quality, /models/status | Pipeline and model execution evidence | Local read |
| GET /api/v1/reports/sales.csv, /reports/management | Filtered CSV / management JSON | Local read |

Analytical filters: `start=YYYY-MM-DD`, `end=YYYY-MM-DD`, `country=...`. Both dates
are inclusive local business dates; reversed ranges return 422. Pagination uses offset
>=0 and limit 1–1000. Customers additionally accept segment/customer_key. Forecast and
model endpoints describe their trained historical scope; they do not silently apply
the sidebar's geographical filters. Those pages state their historical as-of context.

Product sorting accepts `revenue_desc`, `revenue_asc` or `returns_desc`. Monitoring also
exposes timestamped local JUnit summaries; broker/service verification remains separate.
Budget allocations use assumed priorities and conserve the total in pennies.

Write header: `Authorization: Bearer <WRITE_API_TOKEN from ignored .env>`. No default
token is accepted. The Streamlit server uses its local secret for authorised controls;
the token is not embedded in front-end source. The in-process limit is 60 authorised
write requests/client/minute; it is not a distributed production rate limit.

Webhook input uses a 64-character hexadecimal event ID, `source=authorized_webhook`,
invoice, stock_code, optional 24-character pseudonymous customer_key, nonzero integer
quantity, positive finite Decimal unit_price and an explicitly zoned event_time.
External events have no replay_time. Historical events require replay_time. A missing
broker acknowledgement returns 503, not a fabricated 202. Unknown fields are rejected.
Consumer conflicts on an existing event ID with different business values go to DLQ.

Read endpoints have no internet authentication and must remain on loopback or behind
an identity gateway. Database failures return friendly 503 messages and do not reveal
connection credentials. Request IDs and durations are logged without Authorization.
