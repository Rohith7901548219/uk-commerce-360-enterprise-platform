import hmac
import io
import json
import logging
import math
import time
import uuid
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Annotated, Literal

import pandas as pd
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import func, select, text
from sqlalchemy.exc import SQLAlchemyError

from commerce import analytics
from commerce.config import settings
from commerce.db import engine, events, forecasts, initialize, model_logs, predictions, sales
from commerce.observability import recorded_test_summary
from commerce.schemas import HealthResponse, KPIResponse, PageResponse, ReadyResponse, StreamResponse
from commerce.streaming import TransactionEvent, publish, set_state, stream_status

LOGGER = logging.getLogger(__name__)
WRITE_REQUESTS = defaultdict(deque)


@asynccontextmanager
async def lifespan(app):
    initialize()
    yield


app = FastAPI(
    title="UK Commerce 360 Intelligence API",
    version="0.1.0",
    lifespan=lifespan,
    description="Independent portfolio platform. Historical UCI retail data; campaign scenarios are hypothetical.",
)


@app.middleware("http")
async def request_logging(request, call_next):
    started = time.monotonic()
    request_id = uuid.uuid4().hex
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    LOGGER.info(
        json.dumps(
            {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "duration_ms": round((time.monotonic() - started) * 1000, 2),
            }
        )
    )
    return response


@app.exception_handler(SQLAlchemyError)
async def database_error(request, error):
    LOGGER.error("Database operation failed: %s", type(error).__name__)
    return JSONResponse(
        status_code=503,
        content={"detail": "Warehouse unavailable; run initialization and check service health."},
    )


def write_access(request: Request, authorization: Annotated[str | None, Header()] = None):
    secret = settings().write_api_token
    if not secret or not authorization or not hmac.compare_digest(authorization, f"Bearer {secret}"):
        raise HTTPException(401, "Valid write API token required", headers={"WWW-Authenticate": "Bearer"})
    identity = request.client.host if request.client else "local"
    queue = WRITE_REQUESTS[identity]
    now = time.monotonic()
    while queue and now - queue[0] > 60:
        queue.popleft()
    if len(queue) >= 60:
        raise HTTPException(
            429, "Write limit: 60 requests per minute per client", headers={"Retry-After": "60"}
        )
    queue.append(now)


class Filters(BaseModel):
    start: date | None = None
    end: date | None = None
    country: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def dates_ordered(self):
        if self.start and self.end and self.start > self.end:
            raise ValueError("start must precede end")
        return self


def filters(
    start: date | None = None, end: date | None = None, country: str | None = Query(None, max_length=100)
):
    if start and end and start > end:
        raise HTTPException(422, "start must precede end")
    return Filters(start=start, end=end, country=country)


def frame_for(f: Filters):
    return analytics.sales_frame(**f.model_dump())


def records(frame):
    # Convert pandas timestamps and NaN to strict JSON for API clients.
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def page(rows, offset, limit):
    return {"items": rows[offset : offset + limit], "total": len(rows), "offset": offset, "limit": limit}


@app.get("/health", response_model=HealthResponse)
def health():
    return {"status": "ok", "service": "uk-commerce-360", "historical_data": True}


@app.get("/ready", response_model=ReadyResponse)
def ready():
    with engine().connect() as connection:
        connection.execute(text("SELECT 1"))
        count = connection.scalar(select(func.count()).select_from(sales))
    if not count:
        raise HTTPException(503, "Warehouse connected but no accepted sales are loaded")
    return {"status": "ready", "sales_lines": count, "database": engine().dialect.name}


@app.get("/api/v1/kpis", response_model=KPIResponse)
def kpis(f: Annotated[Filters, Depends(filters)]):
    return analytics.kpis(**f.model_dump())


@app.get("/api/v1/sales", response_model=PageResponse)
def list_sales(
    f: Annotated[Filters, Depends(filters)],
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
):
    query = select(sales)
    for key, value in f.model_dump().items():
        if value is not None:
            query = (
                query.where(sales.c.date_key >= value)
                if key == "start"
                else query.where(sales.c.date_key <= value)
                if key == "end"
                else query.where(sales.c.country == value)
            )
    with engine().connect() as connection:
        total = connection.scalar(select(func.count()).select_from(query.subquery()))
        rows = (
            connection.execute(
                query.order_by(sales.c.event_time, sales.c.transaction_id).offset(offset).limit(limit)
            )
            .mappings()
            .all()
        )
    return {"items": [dict(row) for row in rows], "total": total, "offset": offset, "limit": limit}


@app.get("/api/v1/sales/trends")
def sales_trends(f: Annotated[Filters, Depends(filters)], frequency: Literal["D", "W", "MS"] = "D"):
    frame = frame_for(f)
    geography = (
        []
        if frame.empty
        else records(
            frame.groupby("country")
            .amount.sum()
            .rename("net_sales")
            .reset_index()
            .sort_values("net_sales", ascending=False)
        )
    )
    return {"items": records(analytics.trends(frame, frequency)), "geography": geography}


@app.get("/api/v1/customers")
def customer_list(
    f: Annotated[Filters, Depends(filters)],
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    customer_key: str | None = None,
    segment: str | None = None,
):
    frame = frame_for(f)
    result = analytics.rfm(frame)
    if segment:
        result = result[result.segment == segment]
    if customer_key:
        result = result[result.customer_key == customer_key]
    response = page(records(result), offset, limit)
    if customer_key:
        response["timeline"] = records(frame[frame.customer_key == customer_key].sort_values("event_time"))
    return response


@app.get("/api/v1/customers/segments")
def segments(f: Annotated[Filters, Depends(filters)]):
    result = analytics.rfm(frame_for(f))
    summary = (
        result.groupby("segment")
        .agg(
            customers=("customer_key", "count"), revenue=("monetary", "sum"), mean_recency=("recency", "mean")
        )
        .reset_index()
        if not result.empty
        else pd.DataFrame()
    )
    return {
        "items": records(summary),
        "method": "Within-selection RFM percentile scores; positive purchases only",
    }


@app.get("/api/v1/customers/retention")
def customer_retention(f: Annotated[Filters, Depends(filters)]):
    return {
        "items": records(analytics.retention(frame_for(f))),
        "denominator": "Identifiable positive-purchase customers in each first-purchase month",
    }


@app.get("/api/v1/products", response_model=PageResponse)
@app.get("/api/v1/products/performance", response_model=PageResponse)
def product_list(
    f: Annotated[Filters, Depends(filters)],
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    sort: Literal["revenue_desc", "revenue_asc", "returns_desc"] = "revenue_desc",
):
    result = analytics.product_performance(frame_for(f))
    if not result.empty:
        result = result.sort_values(
            "return_unit_rate" if sort == "returns_desc" else "net_sales", ascending=sort == "revenue_asc"
        )
    return page(records(result), offset, limit)


@app.get("/api/v1/products/associations")
def associations(f: Annotated[Filters, Depends(filters)]):
    return {
        "items": analytics.basket_rules(frame_for(f)),
        "scope": "Top 60 merchandise products; min support 0.2%; descriptive co-occurrence, not personalized recommendations",
    }


@app.get("/api/v1/forecasts")
def forecast_list():
    with engine().connect() as connection:
        rows = connection.execute(select(forecasts).order_by(forecasts.c.forecast_date)).mappings().all()
    path = Path("artifacts/forecast_evaluation.json")
    return {
        "items": [dict(x) for x in rows],
        "evaluation": json.loads(path.read_text()) if path.exists() else None,
        "label": "Historical forecast from the end of the dataset; not a present-day revenue forecast",
    }


class PredictionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_keys: list[str] = Field(min_length=1, max_length=100)


@app.post("/api/v1/predictions/repurchase", dependencies=[Depends(write_access)])
def repurchase(body: PredictionRequest):
    with engine().connect() as connection:
        rows = (
            connection.execute(select(predictions).where(predictions.c.customer_key.in_(body.customer_keys)))
            .mappings()
            .all()
        )
    if not rows:
        raise HTTPException(404, "No eligible scored customers found; run model training")
    return {
        "items": [dict(x) for x in rows],
        "label": "30-day repurchase probabilities as of the historical source end",
    }


@app.get("/api/v1/predictions/repurchase")
def prediction_list(offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
    with engine().connect() as connection:
        total = connection.scalar(select(func.count()).select_from(predictions))
        rows = (
            connection.execute(
                select(predictions).order_by(predictions.c.probability.desc()).offset(offset).limit(limit)
            )
            .mappings()
            .all()
        )
    return {"items": [dict(x) for x in rows], "total": total, "offset": offset, "limit": limit}


class ScenarioRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    audience: int = Field(ge=0, le=10000000)
    budget: float = Field(ge=0, le=100000000, allow_inf_nan=False)
    response_rate: float = Field(ge=0, le=1, allow_inf_nan=False)
    incremental_rate: float = Field(ge=0, le=1, allow_inf_nan=False)
    order_value: float = Field(gt=0, le=1000000, allow_inf_nan=False)
    contribution_rate: float = Field(ge=0, le=1, allow_inf_nan=False)


@app.post("/api/v1/scenarios")
def scenarios(body: ScenarioRequest):
    return analytics.scenario(**body.model_dump())


class AllocationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    budget: float = Field(ge=0, le=100000000, allow_inf_nan=False)
    weights: dict[str, float] = Field(min_length=1, max_length=20)

    @model_validator(mode="after")
    def valid_weights(self):
        if (
            any(
                not math.isfinite(value) or value < 0 or value > 100 or len(name) > 80
                for name, value in self.weights.items()
            )
            or sum(self.weights.values()) <= 0
        ):
            raise ValueError("Weights must be finite, between 0 and 100, and have a positive total")
        return self


@app.post("/api/v1/scenarios/allocation")
def budget_allocation(body: AllocationRequest):
    return analytics.allocate_budget(**body.model_dump())


@app.get("/api/v1/data-quality")
def data_quality():
    return analytics.quality_status()


@app.get("/api/v1/models/status")
def models_status():
    with engine().connect() as connection:
        rows = (
            connection.execute(select(model_logs).order_by(model_logs.c.trained_at.desc()).limit(10))
            .mappings()
            .all()
        )
    stability = Path("artifacts/segment_stability.json")
    return {
        "items": [dict(x) for x in rows],
        "segmentation_stability": json.loads(stability.read_text()) if stability.exists() else None,
        "test_summary": recorded_test_summary(),
    }


@app.get("/api/v1/stream/status", response_model=StreamResponse)
def stream_health():
    return stream_status()


@app.get("/api/v1/stream/events", response_model=PageResponse)
def stream_events(offset: int = Query(0, ge=0), limit: int = Query(100, ge=1, le=1000)):
    with engine().connect() as connection:
        total = connection.scalar(select(func.count()).select_from(events))
        rows = (
            connection.execute(
                select(events).order_by(events.c.ingestion_time.desc()).offset(offset).limit(limit)
            )
            .mappings()
            .all()
        )
    return {"items": [dict(x) for x in rows], "total": total, "offset": offset, "limit": limit}


class ReplayControl(BaseModel):
    action: Literal["start", "stop", "pause", "reset"]
    speed: float = Field(default=10, ge=0.1, le=1000, allow_inf_nan=False)


@app.post("/api/v1/stream/control", dependencies=[Depends(write_access)])
def replay_control(body: ReplayControl):
    set_state("control", body.model_dump())
    return {
        "accepted": True,
        "note": "Requires a running replay producer; reset rewinds the cursor and retains deduplicated event history",
    }


@app.post("/api/v1/ingestion/events", status_code=202, dependencies=[Depends(write_access)])
def ingestion(body: TransactionEvent):
    if body.source != "authorized_webhook" or body.replay_time is not None:
        raise HTTPException(422, "Webhook source must be authorized_webhook with no replay_time")
    try:
        publish(body)
    except Exception:
        raise HTTPException(503, "Broker unavailable; event was not acknowledged") from None
    return {
        "accepted": True,
        "event_id": body.event_id,
        "destination": "independent event store; not historical sales facts",
    }


@app.get("/api/v1/reports/sales.csv")
def sales_export(f: Annotated[Filters, Depends(filters)]):
    output = frame_for(f).copy()
    # Mitigate spreadsheet formula injection in text originating from source data.
    for column in output.select_dtypes(include="object").columns:
        output[column] = output[column].map(
            lambda x: "'" + x if isinstance(x, str) and x.startswith(("=", "+", "-", "@")) else x
        )
    return StreamingResponse(
        io.StringIO(output.to_csv(index=False)),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="historical-sales.csv"'},
    )


@app.get("/api/v1/reports/management")
def management_report(f: Annotated[Filters, Depends(filters)]):
    return jsonable_encoder(
        {
            "title": "Historical management report",
            "kpis": analytics.kpis(**f.model_dump()),
            "data_quality": analytics.quality_status(),
            "limitations": [
                "Independent portfolio project",
                "No campaign spend, causal attribution or profit observed",
                "Source ends in December 2011",
            ],
        }
    )
