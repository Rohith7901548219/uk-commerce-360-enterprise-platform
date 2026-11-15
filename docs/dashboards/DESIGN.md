# Application design and reporting specification

The application uses a navy navigation sidebar, a light analytical canvas, accessible
labels, white KPI panels and indigo/teal accents. Charts have table alternatives and
standard Streamlit controls retain keyboard behaviour. Browser screenshots are actual
application captures, not generated illustrations.

The persistent source banner identifies historical data, test fixtures or mirror
provenance. A business date/country selection applies to descriptive analytics. Customer
segment and product selectors refine their own modules. Forecasts and predictions use
the trained dataset scope; they are not recomputed by descriptive sidebar filters.

| Page | Main grain | Decision / caveat |
|---|---|---|
| Executive | Period/country | Reconcile trading; net excludes returns but not costs |
| Revenue | Day/month | Diagnose trends; final source month/day can be incomplete |
| Customer 360 | Identified customer/cohort | Investigate behaviour; missing IDs excluded |
| Product | SKU/invoice basket | Inspect mix/returns; category is heuristic |
| Marketing | Segment/scenario | Design hypotheses; no observed campaign metrics |
| Retention prediction | Customer at source end | Review calibrated ranking, not causal uplift |
| Forecasting | Daily horizon after source end | Compare baselines and uncertainty assumptions |
| Stream monitor | Durable event/worker heartbeat | Genuine metrics only; stale state is unhealthy |
| Scenario simulator | Assumed audience | Sensitivity and break-even, not realised ROI |
| Monitoring | Run/rule/model | Review quality, failures and historical training status |
| About | Methodology | Explain provenance and limits |

Errors show a friendly backend initialization message and expandable diagnostics.
No empty-data page substitutes invented results. Exports provide filtered sales CSV,
management JSON, scenario assumptions and forecast CSV. Data/model execution history is
operational freshness; historical transaction dates are not current data latency.
