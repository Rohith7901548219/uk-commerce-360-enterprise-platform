"""Explicit alternative when UCI DNS is unavailable; never silently used by download_data."""

import hashlib
import json
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from commerce.cli import bootstrap

URL = "https://raw.githubusercontent.com/DiogoRibeiro7/data/main/datasets/online-retail-ii/raw/online_retail_II.xlsx"
METADATA = "https://github.com/DiogoRibeiro7/data/blob/main/datasets/online-retail-ii/metadata.yaml"
EXPECTED = "bcbe73b35f5b7babf197fb0cb983a11f5d9ff929078d4aa53d171b1f2df2e980"


def acquire():
    bootstrap()
    path = Path("data/raw/online_retail_II.mirror.xlsx")
    if not path.exists():
        temporary = path.with_suffix(".part")
        with urllib.request.urlopen(URL, timeout=180) as response, temporary.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
        temporary.replace(path)
    with path.open("rb") as source:
        checksum = hashlib.file_digest(source, "sha256").hexdigest()
    if checksum != EXPECTED:
        raise ValueError("Mirror checksum mismatch; do not ingest this file")
    manifest = {
        "acquisition": "EXPLICIT_THIRD_PARTY_MIRROR",
        "url": URL,
        "metadata_url": METADATA,
        "sha256": checksum,
        "bytes": path.stat().st_size,
        "upstream_verified_directly": False,
        "retrieved_at": datetime.now(UTC).isoformat(),
        "licence": "UCI CC BY 4.0",
        "attribution": "Chen, D. (2012), Online Retail II, UCI, doi:10.24432/C5CG6D",
    }
    path.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))
    print(
        f"Mirror verified against published mirror checksum: {path}; direct upstream verification remains pending"
    )
    return path


if __name__ == "__main__":
    acquire()
