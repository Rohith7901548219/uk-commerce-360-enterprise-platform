import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path


def recorded_test_summary(path=Path("artifacts/tests.xml")):
    if not path.exists():
        return {"available": False, "note": "No recorded local test artifact"}
    try:
        suites = list(ET.parse(path).getroot().iter("testsuite"))
        counts = {
            key: sum(int(suite.attrib.get(key, 0)) for suite in suites)
            for key in ("tests", "failures", "errors", "skipped")
        }
    except (ET.ParseError, OSError, ValueError):
        return {"available": False, "note": "Test report is unavailable or still being written"}
    return {
        "available": True,
        **counts,
        "passed": counts["tests"] - counts["failures"] - counts["errors"] - counts["skipped"],
        "recorded_at": datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat(),
        "note": "Recorded local test run; broker integration is separately qualified in the delivery report",
    }
