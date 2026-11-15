"""Verify actual local HTTP services and save response evidence without secrets."""

import json
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

import httpx

from commerce.config import settings

ENDPOINTS = [
    "/health",
    "/ready",
    "/api/v1/kpis",
    "/api/v1/sales?limit=2",
    "/api/v1/sales/trends?frequency=MS",
    "/api/v1/customers?limit=2",
    "/api/v1/customers/segments",
    "/api/v1/customers/retention",
    "/api/v1/products?limit=2",
    "/api/v1/products?sort=revenue_asc&limit=2",
    "/api/v1/forecasts",
    "/api/v1/predictions/repurchase?limit=2",
    "/api/v1/data-quality",
    "/api/v1/models/status",
    "/api/v1/stream/status",
    "/api/v1/stream/events?limit=2",
    "/openapi.json",
]


def run():
    results = []
    with httpx.Client(timeout=180) as client:
        for endpoint in ENDPOINTS:
            started = perf_counter()
            response = client.get("http://127.0.0.1:8000" + endpoint)
            response.raise_for_status()
            results.append(
                {
                    "endpoint": endpoint,
                    "status": response.status_code,
                    "elapsed_seconds": round(perf_counter() - started, 3),
                }
            )
        ui = client.get("http://127.0.0.1:8501/_stcore/health")
        ui.raise_for_status()
        unauthorized = client.post("http://127.0.0.1:8000/api/v1/stream/control", json={"action": "pause"})
        assert unauthorized.status_code == 401
        scenario = client.post(
            "http://127.0.0.1:8000/api/v1/scenarios",
            json={
                "audience": 1000,
                "budget": 2000,
                "response_rate": 0.1,
                "incremental_rate": 0.5,
                "order_value": 60,
                "contribution_rate": 0.35,
            },
        )
        scenario.raise_for_status()
        assert scenario.json()["estimated_incremental_revenue"] == 3000
        allocation = client.post(
            "http://127.0.0.1:8000/api/v1/scenarios/allocation",
            json={"budget": 100, "weights": {"Test audience A": 1, "Test audience B": 3}},
        )
        allocation.raise_for_status()
        assert sum(item["allocated_budget"] for item in allocation.json()["items"]) == 100
        scored = client.get("http://127.0.0.1:8000/api/v1/predictions/repurchase?limit=1").json()["items"][0]
        inferred = client.post(
            "http://127.0.0.1:8000/api/v1/predictions/repurchase",
            json={"customer_keys": [scored["customer_key"]]},
            headers={"Authorization": f"Bearer {settings().write_api_token}"},
        )
        inferred.raise_for_status()
        assert 0 <= float(inferred.json()["items"][0]["probability"]) <= 1
        backend = client.get("http://127.0.0.1:8000/ready").json()["database"]
    evidence = {
        "verified_at": datetime.now(UTC).isoformat(),
        "endpoints": results,
        "dashboard_health": ui.status_code,
        "unauthenticated_write": unauthorized.status_code,
        "scenario_verified": True,
        "budget_allocation_verified": True,
        "authenticated_historical_prediction_verified": True,
        "database": backend,
        "note": "Individual local checks, not a load-test or SLA claim",
    }
    Path("artifacts/http_verification.json").write_text(json.dumps(evidence, indent=2))
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    run()
