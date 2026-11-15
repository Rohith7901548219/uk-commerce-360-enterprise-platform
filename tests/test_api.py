import pytest


@pytest.mark.parametrize(
    "path",
    [
        "/health",
        "/ready",
        "/api/v1/kpis",
        "/api/v1/sales",
        "/api/v1/sales/trends",
        "/api/v1/customers",
        "/api/v1/customers/segments",
        "/api/v1/customers/retention",
        "/api/v1/products",
        "/api/v1/products/performance",
        "/api/v1/forecasts",
        "/api/v1/data-quality",
        "/api/v1/models/status",
        "/api/v1/stream/status",
        "/api/v1/stream/events",
        "/api/v1/products/associations",
        "/api/v1/reports/management",
        "/api/v1/reports/sales.csv",
        "/openapi.json",
    ],
)
def test_read_routes(client, path):
    response = client.get(path)
    assert response.status_code == 200, response.text
    assert response.headers["X-Request-ID"]


def test_api_validation_and_auth(client):
    assert client.get("/api/v1/sales?limit=1001").status_code == 422
    assert client.get("/api/v1/kpis?start=2011-01-01&end=2010-01-01").status_code == 422
    assert client.post("/api/v1/stream/control", json={"action": "pause"}).status_code == 401
    response = client.post(
        "/api/v1/stream/control",
        json={"action": "pause"},
        headers={"Authorization": "Bearer unit-test-write-token"},
    )
    assert response.status_code == 200
    assert client.post("/api/v1/scenarios", json={"audience": -1}).status_code == 422


def test_hypothetical_scenario_math(client):
    body = {
        "audience": 1000,
        "budget": 2000,
        "response_rate": 0.1,
        "incremental_rate": 0.5,
        "order_value": 60,
        "contribution_rate": 0.35,
    }
    response = client.post("/api/v1/scenarios", json=body)
    assert response.status_code == 200
    result = response.json()
    assert result["expected_incremental_orders"] == 50
    assert result["estimated_incremental_revenue"] == 3000
    assert result["net_contribution_after_spend"] == -950
    assert "HYPOTHETICAL" in result["label"]


def test_pagination_and_customer_privacy(client):
    result = client.get("/api/v1/sales?limit=2&offset=1").json()
    assert result["total"] == 5
    assert len(result["items"]) == 2
    customers = client.get("/api/v1/customers").json()["items"]
    assert all(len(x["customer_key"]) == 24 for x in customers)
    assert all("customer_id" not in x for x in customers)


def test_product_bottom_ranking(client):
    highest = client.get("/api/v1/products?sort=revenue_desc&limit=1").json()["items"][0]
    lowest = client.get("/api/v1/products?sort=revenue_asc&limit=1").json()["items"][0]
    assert highest["stock_code"] == "10002"
    assert lowest["stock_code"] == "10003"
    assert client.get("/api/v1/products?sort=invalid").status_code == 422


def test_budget_allocation_conserves_pennies(client):
    from decimal import Decimal

    response = client.post(
        "/api/v1/scenarios/allocation", json={"budget": 0.02, "weights": {"A": 1, "B": 1, "C": 1, "D": 1}}
    )
    assert response.status_code == 200
    items = response.json()["items"]
    assert sum(Decimal(str(row["allocated_budget"])) for row in items) == Decimal(".02")
    assert all(row["allocated_budget"] >= 0 for row in items)
    assert (
        client.post("/api/v1/scenarios/allocation", json={"budget": 100, "weights": {"A": 0}}).status_code
        == 422
    )
