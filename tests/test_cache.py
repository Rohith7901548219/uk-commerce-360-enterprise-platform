from pathlib import Path

from commerce.analytics import sales_frame
from commerce.ingest import run_pipeline


def add_source(tmp_path, description="Test product"):
    path = tmp_path / "increment.csv"
    path.write_text(
        "Invoice,StockCode,Description,Quantity,InvoiceDate,Price,Customer ID,Country\n"
        f"900001,12345,{description},2,2011-01-01 10:00:00,2.35,42,France\n"
    )
    run_pipeline(Path(path), fixture=True)


def test_cache_invalidates_on_successful_import_and_preserves_filters(warehouse, tmp_path):
    before = sales_frame()
    assert len(before) == 6
    add_source(tmp_path)
    after = sales_frame()
    assert len(after) == 7
    assert len(sales_frame(country="France")) == 3
    assert (sales_frame(include_returns=False).quantity > 0).all()


def test_csv_formula_escaping_does_not_mutate_analytics_cache(client, tmp_path):
    add_source(tmp_path, "=2+2")
    response = client.get("/api/v1/reports/sales.csv")
    assert response.status_code == 200
    assert "'=2+2" in response.text
    products = client.get("/api/v1/products").json()["items"]
    assert any(row["description"] == "=2+2" for row in products)
