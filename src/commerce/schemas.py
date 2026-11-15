"""Public response contracts; source customer identifiers are deliberately absent."""

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: Literal["ok"]
    service: str
    historical_data: bool


class ReadyResponse(BaseModel):
    status: Literal["ready"]
    sales_lines: int = Field(ge=1)
    database: str


class KPIResponse(BaseModel):
    gross_sales: float
    returns: float
    net_sales: float
    orders: int
    identifiable_customers: int
    sales_lines: int
    return_lines: int
    average_order_value: float
    repeat_purchase_rate: float = Field(ge=0, le=1)
    currency: Literal["GBP"]
    data_label: str
    sources: list[dict[str, Any]]
    date_min: date | None
    date_max: date | None
    countries: list[str]


class PageResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=1000)


class StreamResponse(BaseModel):
    label: str
    counts: dict[str, int]
    events_ingested: int
    processed: int
    rejected: int
    throughput_per_second_last_minute: float
    last_ingestion_time: datetime | None
    consumer: dict[str, Any]
    producer: dict[str, Any]
    control: dict[str, Any]
    healthy: bool
    consumer_lag: int | None
