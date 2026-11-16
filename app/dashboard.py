"""Eleven-page Streamlit client; every metric is fetched from the FastAPI backend."""

import json
from datetime import date

import httpx
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from commerce.config import settings

st.set_page_config(
    page_title="UK Commerce 360° Intelligence", page_icon="◈", layout="wide", initial_sidebar_state="expanded"
)
st.markdown(
    """<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap');
html, body, [class*="css"], [data-testid="stApp"] {font-family:'DM Sans',sans-serif;}
[data-testid="stApp"] {background:#f5f6fa;color:#17243b;}
[data-testid="stSidebar"] {background:#111d33;}
[data-testid="stSidebar"] * {color:#e4eaf5;}
[data-testid="stSidebar"] input {color:#17243b!important;-webkit-text-fill-color:#17243b!important;}
[data-testid="stSidebar"] [data-baseweb="select"] div, [data-testid="stSidebar"] [data-baseweb="select"] span {color:#17243b!important;}
[data-testid="stSidebar"] button p {color:#17243b!important;}
[data-testid="stMetric"] {background:white;border:1px solid #e4e8ef;border-radius:12px;padding:19px 22px;}
[data-testid="stMetricLabel"] {color:#66738b;font-size:.85rem;}
[data-testid="stMetricValue"] {font-size:1.85rem;font-weight:700;color:#15243e;}
h1 {font-size:2.1rem!important;letter-spacing:-1px;font-weight:700!important;}
h2 {font-size:1.35rem!important;} h3 {font-size:1.05rem!important;}
.eyebrow {font-size:.75rem;letter-spacing:2px;color:#63738f;font-weight:700;}
.hero {background:#15243e;border-radius:16px;padding:24px 30px;color:white;margin:10px 0 24px;}
.hero h2 {color:white;margin:0;padding:0;font-size:1.4rem!important;}
.hero p {color:#bfccdf;margin:8px 0 0;font-size:.9rem;}
.tag {background:#e8f5f2;color:#177869;border-radius:20px;padding:5px 12px;font-size:.72rem;font-weight:600;}
.stPlotlyChart {background:white;border:1px solid #e4e8ef;border-radius:12px;overflow:hidden;}
[data-testid="stDataFrame"] {border:1px solid #e4e8ef;border-radius:12px;}
.stButton button {border-radius:8px;}
</style>""",
    unsafe_allow_html=True,
)

PAGES = [
    "Executive Overview",
    "Revenue Analytics",
    "Customer 360°",
    "Product Intelligence",
    "Marketing Intelligence",
    "Retention Prediction",
    "Revenue Forecasting",
    "Real-Time Transaction Monitor",
    "Business Scenario Simulator",
    "Data Engineering & Model Monitoring",
    "About / Architecture / Data Methodology",
]
COLORS = ["#4465df", "#26a591", "#efad54", "#a281d3", "#e57f83"]
px.defaults.template = "plotly_white"
px.defaults.color_discrete_sequence = COLORS


@st.cache_data(ttl=45, show_spinner=False)
def get(path, params=None):
    response = httpx.get(settings().api_base_url + path, params=params, timeout=180)
    response.raise_for_status()
    return response.json()


def post(path, body, authenticated=False):
    headers = {"Authorization": f"Bearer {settings().write_api_token}"} if authenticated else {}
    response = httpx.post(settings().api_base_url + path, json=body, headers=headers, timeout=30)
    response.raise_for_status()
    get.clear()
    return response.json()


def chart(figure, height=330):
    figure.update_layout(
        height=height,
        margin=dict(l=18, r=20, t=45, b=70),
        font=dict(family="DM Sans", color="#53637c"),
        paper_bgcolor="white",
        plot_bgcolor="white",
        legend=dict(orientation="h", y=-0.2),
        title_font=dict(size=15, color="#17243b"),
    )
    figure.update_xaxes(showgrid=False)
    figure.update_yaxes(gridcolor="#edf0f5", zeroline=False)
    st.plotly_chart(figure, width="stretch")


def table(items, currency=None):
    frame = pd.DataFrame(items)
    if frame.empty:
        st.info("No processed records match this selection.")
    else:
        st.dataframe(frame, hide_index=True, width="stretch")
    return frame


def money(value):
    return f"£{value:,.0f}"


with st.sidebar:
    st.markdown("## ◈ UK COMMERCE\n**360° INTELLIGENCE**")
    st.caption("ENTERPRISE ANALYTICS WORKSPACE")
    selected = st.radio("Workspace", PAGES, label_visibility="collapsed")
    st.divider()
    st.caption(
        "INDEPENDENT PORTFOLIO PROJECT\n\nHistorical retail intelligence.\nNo real-time commercial activity claimed."
    )

try:
    meta = get("/api/v1/kpis")
    with st.sidebar:
        st.markdown("**Analysis filters**")
        minimum = date.fromisoformat(meta["date_min"]) if meta["date_min"] else date(2009, 12, 1)
        maximum = date.fromisoformat(meta["date_max"]) if meta["date_max"] else date(2011, 12, 9)
        selected_dates = st.date_input(
            "Transaction period", value=(minimum, maximum), min_value=minimum, max_value=maximum
        )
        country = st.selectbox("Market", ["All markets"] + meta["countries"])
        if st.button("Refresh backend data", width="stretch"):
            get.clear()
            st.rerun()
    filters = {"country": country} if country != "All markets" else {}
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        filters.update(start=selected_dates[0].isoformat(), end=selected_dates[1].isoformat())
    st.markdown(
        '<div class="eyebrow">COMMERCE INTELLIGENCE / ANALYTICS WORKSPACE</div>', unsafe_allow_html=True
    )
    left, right = st.columns([4, 1])
    left.title(selected)
    right.markdown(f'<br><span class="tag">● {meta["data_label"]}</span>', unsafe_allow_html=True)
    st.caption(
        f"{minimum:%d %b %Y} — {maximum:%d %b %Y} · GBP · Source: UCI Online Retail II · Historical analysis"
    )
    if meta["data_label"] == "TEST FIXTURE":
        st.warning(
            "TEST FIXTURE DATA — these values are for automated validation, not real business results."
        )
    elif "MIRROR" in meta["data_label"]:
        st.caption(
            "Acquired from a publicly attributed UCI mirror; checksum recorded. Direct UCI retrieval remains unverified on this host."
        )

    if selected in ("Executive Overview", "Revenue Analytics"):
        metrics = get("/api/v1/kpis", filters)
        if selected == "Executive Overview":
            st.markdown(
                '<div class="hero"><h2>A complete view of historical commerce.</h2><p>Understand revenue, customers and products through one reconciled analytical workspace.</p></div>',
                unsafe_allow_html=True,
            )
        columns = st.columns(4)
        for column, label, value in zip(
            columns,
            ["Net sales", "Gross sales", "Returns", "Total orders"],
            [
                money(metrics["net_sales"]),
                money(metrics["gross_sales"]),
                money(metrics["returns"]),
                f"{metrics['orders']:,}",
            ],
            strict=True,
        ):
            column.metric(label, value)
        st.write("")
        columns = st.columns(3)
        columns[0].metric("Identifiable customers", f"{metrics['identifiable_customers']:,}")
        columns[1].metric("Average order value · gross", money(metrics["average_order_value"]))
        columns[2].metric("Repeat-purchase rate", f"{metrics['repeat_purchase_rate']:.1%}")
        data = get(
            "/api/v1/sales/trends",
            {**filters, "frequency": "MS" if selected == "Executive Overview" else "D"},
        )
        daily = pd.DataFrame(data["items"])
        a, b = st.columns([2, 1])
        with a:
            if not daily.empty:
                chart(
                    px.area(
                        daily,
                        x="date",
                        y="net_sales",
                        title="Revenue trajectory",
                        labels={"net_sales": "Net sales · GBP", "date": ""},
                    )
                )
        with b:
            geo = pd.DataFrame(data["geography"]).head(7)
            if not geo.empty:
                chart(
                    px.bar(
                        geo.sort_values("net_sales"),
                        x="net_sales",
                        y="country",
                        orientation="h",
                        title="Revenue by market",
                        labels={"country": "", "net_sales": "GBP"},
                    )
                )
        a, b = st.columns([1.4, 1])
        with a:
            st.subheader("Products driving revenue")
            table(get("/api/v1/products/performance", {**filters, "limit": 8})["items"])
        with b:
            segments = pd.DataFrame(get("/api/v1/customers/segments", filters)["items"])
            if not segments.empty:
                chart(
                    px.pie(
                        segments,
                        names="segment",
                        values="revenue",
                        hole=0.65,
                        title="Positive sales by customer segment",
                    )
                )
        st.caption(
            "Gross sales = accepted positive purchases. Returns are positive deductions. AOV uses gross sales / positive-purchase invoices. Repeat rate uses identifiable customers only."
        )
        report = get("/api/v1/reports/management", filters)
        st.download_button(
            "Export management report · JSON",
            json.dumps(report, indent=2),
            "management-report.json",
            "application/json",
        )
        if st.button("Prepare filtered sales CSV"):
            response = httpx.get(
                settings().api_base_url + "/api/v1/reports/sales.csv", params=filters, timeout=180
            )
            response.raise_for_status()
            st.download_button("Download sales CSV", response.content, "historical-sales.csv", "text/csv")

    elif selected == "Customer 360°":
        segments = get("/api/v1/customers/segments", filters)
        selected_segment = st.selectbox(
            "Customer segment", ["All segments"] + [x["segment"] for x in segments["items"]]
        )
        params = {**filters, "limit": 1000}
        if selected_segment != "All segments":
            params["segment"] = selected_segment
        result = get("/api/v1/customers", params)
        st.caption(f"{result['total']:,} eligible customers · first 1,000 shown · pseudonymized identifiers")
        table(result["items"])
        keys = [x["customer_key"] for x in result["items"]]
        if keys:
            key = st.selectbox("Explore a customer's purchasing history", keys)
            customer = get("/api/v1/customers", {**filters, "customer_key": key})
            timeline = pd.DataFrame(customer["timeline"])
            if not timeline.empty:
                chart(
                    px.scatter(
                        timeline,
                        x="event_time",
                        y="amount",
                        color="description",
                        title="Purchase and return timeline",
                        labels={"amount": "GBP"},
                    )
                )
                table(customer["timeline"])
        retention = pd.DataFrame(get("/api/v1/customers/retention", filters)["items"])
        if not retention.empty:
            matrix = retention.pivot(index="cohort", columns="period", values="retention_rate")
            chart(
                px.imshow(
                    matrix,
                    text_auto=".0%",
                    color_continuous_scale="Blues",
                    aspect="auto",
                    title="Observed customer cohort retention",
                ),
                470,
            )
            st.caption(
                "Empty cells are unobserved future periods. Cohorts are defined within the selected period."
            )

    elif selected == "Product Intelligence":
        ranking = st.selectbox(
            "Product ranking", ["Highest net sales", "Lowest net sales", "Highest return unit rate"]
        )
        ordering = {
            "Highest net sales": "revenue_desc",
            "Lowest net sales": "revenue_asc",
            "Highest return unit rate": "returns_desc",
        }
        products = get("/api/v1/products/performance", {**filters, "limit": 1000, "sort": ordering[ranking]})
        frame = pd.DataFrame(products["items"])
        if not frame.empty:
            codes = st.multiselect("Focus products", frame.stock_code.tolist())
            shown = frame[frame.stock_code.isin(codes)] if codes else frame
            chart(
                px.bar(
                    shown.head(15),
                    x="description",
                    y="return_unit_rate" if ranking == "Highest return unit rate" else "net_sales",
                    title=f"{ranking} - product comparison",
                    labels={"net_sales": "GBP", "return_unit_rate": "Return unit rate (fraction)"},
                )
            )
            table(shown.to_dict("records"))
            st.caption(
                f"{products['total']:,} products in selection; first 1,000 available in this view. Returns may relate to purchases before the selected period."
            )
        with st.expander("Frequently purchased combinations · support, confidence and lift"):
            if st.button("Calculate basket associations"):
                rules = get("/api/v1/products/associations", filters)
                st.caption(rules["scope"])
                table(rules["items"])

    elif selected in ("Marketing Intelligence", "Business Scenario Simulator"):
        st.info(
            "HYPOTHETICAL SCENARIO — the source contains no advertising spend, campaign assignment, attribution or profit data."
        )
        if selected == "Marketing Intelligence":
            segment_rows = get("/api/v1/customers/segments", filters)["items"]
            table(segment_rows)
            st.markdown(
                "**Audience priorities:** investigate retention for high-value at-risk customers; test replenishment messaging for loyal buyers; validate onboarding for recent customers. These are recommendations to test, with no uplift claimed."
            )
            with st.expander("Allocate a hypothetical budget across segments"):
                with st.form("budget_allocation"):
                    total_budget = st.number_input(
                        "Assumed total allocation budget - GBP", 0.0, 100000000.0, 5000.0
                    )
                    weights = {
                        row["segment"]: st.slider(f"Assumed priority: {row['segment']}", 0, 5, 1)
                        for row in segment_rows
                    }
                    allocate = st.form_submit_button("Calculate allocation")
                if allocate and weights:
                    if not any(weights.values()):
                        st.info("Choose at least one positive segment priority.")
                    else:
                        allocation = post(
                            "/api/v1/scenarios/allocation", {"budget": total_budget, "weights": weights}
                        )
                        st.caption(allocation["label"])
                        table(allocation["items"])
        with st.form("scenario"):
            a, b, c = st.columns(3)
            audience = a.number_input("Assumed audience", 0, 10000000, 1000)
            budget = b.number_input("Assumed budget · GBP", 0.0, 100000000.0, 2000.0)
            order_value = c.number_input("Assumed order value · GBP", 1.0, 1000000.0, 60.0)
            response = a.slider("Assumed response rate", 0.0, 1.0, 0.1)
            incremental = b.slider("Assumed incremental share", 0.0, 1.0, 0.5)
            contribution = c.slider("Assumed contribution rate", 0.0, 1.0, 0.35)
            submitted = st.form_submit_button("Calculate scenario")
        if submitted:
            result = post(
                "/api/v1/scenarios",
                {
                    "audience": audience,
                    "budget": budget,
                    "response_rate": response,
                    "incremental_rate": incremental,
                    "order_value": order_value,
                    "contribution_rate": contribution,
                },
            )
            a, b, c = st.columns(3)
            a.metric("Estimated incremental orders", f"{result['expected_incremental_orders']:,.1f}")
            b.metric("Estimated incremental revenue", money(result["estimated_incremental_revenue"]))
            c.metric("Assumed net contribution", money(result["net_contribution_after_spend"]))
            sensitivity = [
                post(
                    "/api/v1/scenarios",
                    {
                        "audience": audience,
                        "budget": budget,
                        "response_rate": r / 100,
                        "incremental_rate": incremental,
                        "order_value": order_value,
                        "contribution_rate": contribution,
                    },
                )
                for r in range(0, 51, 5)
            ]
            chart(
                px.line(
                    x=list(range(0, 51, 5)),
                    y=[x["net_contribution_after_spend"] for x in sensitivity],
                    labels={"x": "Assumed response rate · %", "y": "Assumed net contribution · GBP"},
                    title="Sensitivity to response assumptions",
                )
            )
            st.download_button(
                "Export scenario assumptions", json.dumps(result, indent=2), "hypothetical-scenario.json"
            )

    elif selected == "Retention Prediction":
        st.caption("Scored at the historical dataset end. Probabilities do not describe current customers.")
        status = get("/api/v1/models/status")
        runs = [x for x in status["items"] if x["model_type"] == "repurchase"]
        if runs:
            report = runs[0]["metrics"]
            winner = report["selected_model"]
            st.success(f"Selected by validation PR-AUC: {winner.replace('_', ' ').title()}")
            scores = report["models"][winner]["test"]
            for column, metric in zip(st.columns(4), ["pr_auc", "roc_auc", "f1", "brier_score"], strict=True):
                column.metric(
                    metric.replace("_", " ").upper(),
                    f"{scores[metric]:.3f}" if scores[metric] is not None else "N/A",
                )
            table(
                [
                    {
                        "model": name,
                        **{k: v for k, v in result["test"].items() if isinstance(v, (float, int))},
                    }
                    for name, result in report["models"].items()
                ]
            )
            calibration = scores["calibration"]
            figure = go.Figure(
                go.Scatter(
                    x=calibration["mean_probability"],
                    y=calibration["fraction_positive"],
                    mode="lines+markers",
                    name="Observed calibration",
                )
            )
            figure.add_trace(
                go.Scatter(
                    x=[0, 1], y=[0, 1], mode="lines", name="Perfect calibration", line=dict(dash="dash")
                )
            )
            figure.update_layout(
                title="Repurchase probability calibration",
                xaxis_title="Mean predicted probability",
                yaxis_title="Observed positive rate",
            )
            chart(figure)
            table(get("/api/v1/predictions/repurchase", {"limit": 100})["items"])
            with st.expander("Temporal splits, leakage controls and model limitations"):
                st.json(
                    {
                        "split": report["split"],
                        "limitations": report["limitations"],
                        "feature_importance": report["permutation_importance_test"],
                    }
                )
        else:
            st.info(
                "No evaluated model is available. Run the model training command after real-data ingestion."
            )

    elif selected == "Revenue Forecasting":
        result = get("/api/v1/forecasts")
        st.info(result["label"])
        forecast = pd.DataFrame(result["items"])
        if not forecast.empty:
            report = result["evaluation"]
            st.caption(f"Selected: {report['selected_model']} · {report['interval_method']}")
            figure = go.Figure()
            figure.add_trace(
                go.Scatter(x=forecast.forecast_date, y=forecast.upper, line=dict(width=0), showlegend=False)
            )
            figure.add_trace(
                go.Scatter(
                    x=forecast.forecast_date,
                    y=forecast.lower,
                    fill="tonexty",
                    fillcolor="rgba(68,101,223,.14)",
                    line=dict(width=0),
                    name="Approximate uncertainty band",
                )
            )
            figure.add_trace(
                go.Scatter(
                    x=forecast.forecast_date,
                    y=forecast.prediction,
                    line=dict(color=COLORS[0], width=3),
                    name="Forecast",
                )
            )
            figure.update_layout(title="28-day historical net-revenue forecast", yaxis_title="GBP")
            chart(figure, 410)
            table(
                [
                    {"model": name, "development_mae": values["development_mae"], **values["folds"][-1]}
                    for name, values in report["models"].items()
                ]
            )
            actuals = pd.DataFrame(report["test_comparison"])
            actuals = actuals[actuals.model == report["selected_model"]]
            chart(
                px.line(
                    actuals,
                    x="date",
                    y=["actual", "prediction"],
                    title="Untouched final test horizon · actual versus forecast",
                )
            )
            st.download_button(
                "Export forecast CSV",
                forecast.to_csv(index=False),
                "historical-revenue-forecast.csv",
                "text/csv",
            )
        else:
            st.info("Train forecasting models to populate this page.")

    elif selected == "Real-Time Transaction Monitor":
        st.warning("HISTORICAL TRANSACTION REPLAY — DEMONSTRATION")

        @st.fragment(run_every="5s")
        def monitor():
            get.clear()
            status = get("/api/v1/stream/status")
            a, b, c, d = st.columns(4)
            a.metric("Events stored", status["events_ingested"])
            b.metric("Processed", status["processed"])
            c.metric("Rejected", status["rejected"])
            d.metric("Observed events / second", f"{status['throughput_per_second_last_minute']:.2f}")
            st.caption(
                f"Consumer health: {'active' if status['healthy'] else 'not observed / stale'} · Consumer lag: {status['consumer_lag']} · Last ingestion: {status['last_ingestion_time']}"
            )
            table(get("/api/v1/stream/events", {"limit": 20})["items"])
            with st.expander("Actual worker state"):
                st.json(status)

        monitor()
        speed = st.slider("Replay events per second", 1, 100, 10)
        for column, action in zip(st.columns(4), ["start", "pause", "stop", "reset"], strict=True):
            if column.button(action.title(), width="stretch"):
                st.info(
                    post("/api/v1/stream/control", {"action": action, "speed": speed}, authenticated=True)[
                        "note"
                    ]
                )
        st.caption(
            "Controls require the producer service. Reset rewinds the source cursor; deterministic event IDs protect existing counts. The event store never updates historical sales totals."
        )

    elif selected == "Data Engineering & Model Monitoring":
        result = get("/api/v1/data-quality")
        st.caption(result["label"])
        metrics = result["metrics"]
        for column, key in zip(
            st.columns(4), ["imported", "accepted", "quarantined", "duplicate"], strict=True
        ):
            column.metric(key.title(), f"{metrics.get(key, 0):,}")
        table([{"rule": key, "records": value} for key, value in metrics.items()])
        st.subheader("Pipeline execution history")
        table([{k: v for k, v in run.items() if k != "details"} for run in result["runs"]])
        st.subheader("Model execution history")
        models = get("/api/v1/models/status")
        summary = models.get("test_summary", {})
        if summary.get("available"):
            st.caption(
                f"Recorded automated test run: {summary['passed']} passed / {summary['tests']} total; {summary['failures']} failures, {summary['errors']} errors. Recorded {summary['recorded_at']}."
            )
            st.caption(summary["note"])
        table([{k: v for k, v in model.items() if k != "metrics"} for model in models["items"]])
        if models["segmentation_stability"]:
            st.json(models["segmentation_stability"])
        with st.expander("Operational source provenance"):
            st.json(meta["sources"])

    else:
        st.markdown("""### Evidence-led historical intelligence
This independent portfolio project analyses **Online Retail II**, a UK-based retailer's
transactions from **2009–2011**. Source: Daqing Chen, UCI Machine Learning Repository,
[DOI 10.24432/C5CG6D](https://doi.org/10.24432/C5CG6D), **CC BY 4.0**.

**Data path:** official workbook → immutable raw rows → validated staging → star schema →
analytical services / dbt marts / models → FastAPI → this application.

**Streaming path:** historical producer → real Redpanda broker → validated consumer →
independent event store. Event time, replay time and ingestion time are separate.

**Methodology:** decimals for money; cancellations and negative quantities form returns;
invalid rows are quarantined; duplicates remain auditable; unidentified customers stay in
sales totals but are excluded from customer models. Customer IDs use keyed HMAC pseudonyms.

**Models:** chronological snapshots with a label-horizon embargo; baseline comparisons;
validation-based selection; untouched final forecast test horizon; measured calibration.

**Limits:** no cost, profit, campaign spend, attribution or experimental data exists in this
source. Scenario values are user assumptions. No commercial deployment, real customers,
financial uplift or present-day forecasting validity is claimed.

**Read API:** [OpenAPI / Swagger](http://127.0.0.1:8000/docs). Full methodology, business
requirements, Power BI assets and deployment instructions are in the repository docs.
""")

except (httpx.HTTPError, KeyError, ValueError) as error:
    st.error(
        "The analytical backend is unavailable or still initializing. Start the API and complete data ingestion, then refresh."
    )
    with st.expander("Diagnostic details"):
        st.code(str(error))
