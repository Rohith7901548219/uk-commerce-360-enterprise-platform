from pathlib import Path

import pytest
from openpyxl import Workbook

from commerce.ingest import run_pipeline


def test_excel_aliases_and_cross_sheet_duplicates(warehouse, tmp_path):
    workbook = Workbook()
    first = workbook.active
    first.append(
        [
            "InvoiceNo",
            "StockCode",
            "Description",
            "Quantity",
            "InvoiceDate",
            "UnitPrice",
            "CustomerID",
            "Country",
        ]
    )
    values = ["900001", "12345", "Test product", 1, "2011-01-01 10:00:00", 3.5, 99, "France"]
    first.append(values)
    second = workbook.create_sheet("second")
    second.append(
        ["Invoice", "StockCode", "Description", "Quantity", "InvoiceDate", "Price", "Customer ID", "Country"]
    )
    second.append(values)
    path = tmp_path / "source.xlsx"
    workbook.save(path)
    result = run_pipeline(path, fixture=True, chunk_size=1)
    assert result["imported"] == 2
    assert result["accepted"] == 1
    assert result["duplicate"] == 1
    assert result["reconciled"] == 1


def test_unknown_workbook_headers_fail_loudly(warehouse, tmp_path):
    workbook = Workbook()
    workbook.active.append(["unrecognised", "schema"])
    path = tmp_path / "bad.xlsx"
    workbook.save(path)
    with pytest.raises(ValueError, match="Unknown source headers"):
        run_pipeline(Path(path), fixture=True)
    from commerce.analytics import quality_status

    failure = quality_status()["runs"][0]
    assert failure["status"] == "FAILED"
    assert failure["details"]["error_type"] == "ValueError"
    assert "unrecognised" not in str(failure["details"])
