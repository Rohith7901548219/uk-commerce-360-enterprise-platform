"""Capture only actual running pages, never generated dashboard mockups."""

import json
from pathlib import Path

from playwright.sync_api import sync_playwright

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
COMPLETE_MARKERS = [
    "Export management report",
    "Export management report",
    "Empty cells are unobserved future periods",
    "Frequently purchased combinations",
    "Calculate scenario",
    "Temporal splits, leakage controls and model limitations",
    "Export forecast CSV",
    "Controls require the producer service",
    "Calculate scenario",
    "Operational source provenance",
    "No commercial deployment, real customers",
]


def run():
    output = Path("docs/screenshots")
    output.mkdir(parents=True, exist_ok=True)
    results = []
    with sync_playwright() as driver:
        browser = driver.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1100}, device_scale_factor=1)
        page.goto("http://127.0.0.1:8501", wait_until="domcontentloaded", timeout=60000)
        for index, name in enumerate(PAGES):
            page.get_by_text(name, exact=True).first.click(timeout=120000)
            page.get_by_role("heading", name=name, exact=True).wait_for(timeout=120000)
            # A new heading appears before old Streamlit elements are removed. Require
            # the page's final content marker and absence of stale elements as well.
            page.get_by_text(COMPLETE_MARKERS[index], exact=False).last.wait_for(
                state="attached", timeout=180000
            )
            page.wait_for_function("!document.querySelector('[data-stale=\"true\"]')", timeout=180000)
            page.wait_for_timeout(500)
            errors = page.locator('[data-testid="stException"]').all_text_contents()
            if errors:
                raise AssertionError(f"{name}: {errors}")
            if index in (0, 2, 5, 6, 9):
                page.screenshot(
                    path=str(
                        output / f"{index + 1:02d}-{name.lower().replace(' ', '-').replace('°', '')}.png"
                    ),
                    full_page=True,
                )
            results.append(
                {
                    "page": name,
                    "exception_count": len(errors),
                    "completion_marker": COMPLETE_MARKERS[index],
                    "url": page.url,
                }
            )
        browser.close()
    Path("artifacts/browser_smoke.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    run()
