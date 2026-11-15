"""Check staged documentation and accidental local-secret inclusion; never print secrets."""

import json
import re
import shutil
import subprocess
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
GIT = shutil.which("git") or "C:/Program Files/Git/cmd/git.exe"


def run():
    paths = subprocess.check_output([GIT, "ls-files", "-z"], cwd=ROOT).decode("utf-8").split("\0")
    paths = [path for path in paths if path]
    secrets = dotenv_values(ROOT / ".env")
    forbidden = [
        secrets.get(key, "").encode()
        for key in ("WRITE_API_TOKEN", "CUSTOMER_HASH_KEY", "POSTGRES_PASSWORD")
        if secrets.get(key)
    ]
    errors = []
    for relative in paths:
        if relative == ".env" or relative.startswith(
            (".tools/", ".venv/", "data/raw/", "data/warehouse/", "artifacts/", ".local/")
        ):
            errors.append(f"Generated/private path staged: {relative}")
        path = ROOT / relative
        content = path.read_bytes()
        if any(secret in content for secret in forbidden):
            errors.append(f"Local secret detected in {relative}")
        if path.suffix == ".md":
            for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content.decode("utf-8")):
                if link.startswith(("http:", "https:", "mailto:", "#")):
                    continue
                target = link.split("#")[0].strip("<>")
                if target and not (path.parent / target).exists():
                    errors.append(f"Broken local link in {relative}: {target}")
    if errors:
        raise ValueError("\n".join(errors))
    evidence = {
        "tracked_files_checked": len(paths),
        "generated_private_paths_staged": 0,
        "local_secret_matches": 0,
        "broken_local_markdown_links": 0,
        "scope": "Exact local secret values and local documentation links; not a comprehensive security audit",
    }
    Path("artifacts/repository_check.json").write_text(json.dumps(evidence, indent=2))
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    run()
