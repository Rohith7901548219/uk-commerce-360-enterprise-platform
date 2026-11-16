"""Review publication candidates and all reachable history without exposing secret values."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
GIT = shutil.which("git") or "C:/Program Files/Git/cmd/git.exe"
PRIVATE_PREFIXES = (
    ".tools/",
    ".venv/",
    "venv/",
    ".local/",
    "artifacts/",
    "mlruns/",
    "mlartifacts/",
    "node_modules/",
    "logs/",
    "data/raw/",
    "data/private/",
    "data/downloads/",
    "data/warehouse/",
    "data/processed/",
    ".aws/",
    ".azure/",
    ".ssh/",
)
PRIVATE_SUFFIXES = {
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pkl",
    ".joblib",
    ".onnx",
    ".xlsx",
    ".xls",
    ".csv",
    ".parquet",
    ".pem",
    ".key",
    ".pfx",
    ".p12",
    ".log",
}
REVIEWED_FIXTURE = "data/fixtures/retail.csv"
PATTERNS = {
    "github_token": re.compile(rb"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})"),
    "aws_access_key": re.compile(rb"(?:AKIA|ASIA)[A-Z0-9]{16}"),
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "openai_api_key": re.compile(rb"sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{35,}"),
    "azure_sas_signature": re.compile(rb"[?&]sig=[A-Za-z0-9%+/]{24,}"),
    "azure_storage_key": re.compile(rb"AccountKey=[A-Za-z0-9+/]{60,}={0,2}"),
}


def git(*arguments):
    return subprocess.check_output([GIT, *arguments], cwd=ROOT)


def private_path(path):
    name = Path(path).name
    return (
        path.startswith(PRIVATE_PREFIXES)
        or (name.startswith(".env") and name != ".env.example")
        or (Path(path).suffix.lower() in PRIVATE_SUFFIXES and path != REVIEWED_FIXTURE)
    )


def local_secret_values():
    values = set()
    # Read only workspace configuration and specifically named process credentials.
    for path in ROOT.glob(".env*"):
        if path.name == ".env.example" or not path.is_file():
            continue
        for name, value in dotenv_values(path).items():
            if (
                value
                and len(value) >= 8
                and re.search(r"TOKEN|SECRET|PASSWORD|API_KEY|HASH_KEY|CONNECTION_STRING", name, re.I)
            ):
                values.add(value.encode())
    for name in (
        "GH_TOKEN",
        "GITHUB_TOKEN",
        "OPENAI_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AZURE_CLIENT_SECRET",
        "AZURE_STORAGE_CONNECTION_STRING",
    ):
        if value := os.environ.get(name):
            values.add(value.encode())
    return values


def scan_blob(content, secret_values):
    rules = [name for name, pattern in PATTERNS.items() if pattern.search(content)]
    if any(value in content for value in secret_values):
        rules.append("exact_local_secret")
    return rules


def audit():
    secret_values = local_secret_values()
    # Untracked, unignored files are candidates too; ignored local data stays on disk.
    tracked = {path for path in git("ls-files", "-z").decode().split("\0") if path}
    untracked = {
        path for path in git("ls-files", "--others", "--exclude-standard", "-z").decode().split("\0") if path
    }
    candidates = sorted(tracked | untracked)
    findings, history_findings, broken_links = [], [], []
    for relative in candidates:
        path = ROOT / relative
        if not path.is_file():
            continue
        if private_path(relative):
            findings.append({"path": relative, "rule": "private_or_generated_path"})
        content = path.read_bytes()
        for rule in scan_blob(content, secret_values):
            findings.append({"path": relative, "rule": rule})
        if relative == REVIEWED_FIXTURE:
            # This exception is narrow: nine synthetic rows, no arbitrary replacement dataset.
            if len(content.splitlines()) != 10 or len(content) > 2048 or b"Blue ceramic mug" not in content:
                findings.append({"path": relative, "rule": "fixture_requires_manual_review"})
        if path.suffix == ".md":
            for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content.decode("utf-8")):
                if link.startswith(("https:", "http:", "mailto:", "#")):
                    continue
                target = link.split("#")[0].strip("<>")
                if target and not (path.parent / target).exists():
                    broken_links.append({"path": relative, "target": target})
    history_lines = git("rev-list", "--objects", "--all").decode().splitlines()
    objects = [line.split(" ", 1) for line in history_lines]
    # A single batched Git process avoids spawning one process per historical object.
    query = "\n".join(row[0] for row in objects).encode() + b"\n"
    batch = subprocess.run(
        [GIT, "cat-file", "--batch"], input=query, capture_output=True, cwd=ROOT, check=True
    ).stdout
    cursor = 0
    blobs = 0
    for row in objects:
        end = batch.index(b"\n", cursor)
        header = batch[cursor:end].split()
        size = int(header[2])
        content = batch[end + 1 : end + 1 + size]
        cursor = end + 2 + size
        if header[1] != b"blob":
            continue
        blobs += 1
        relative = row[1] if len(row) > 1 else "unknown"
        rules = scan_blob(content, secret_values)
        if private_path(relative):
            rules.append("historical_private_or_generated_path")
        for rule in rules:
            history_findings.append({"object": row[0][:12], "path": relative, "rule": rule})
    inventory = Counter()
    for directory, child_directories, files in os.walk(ROOT):
        relative_directory = Path(directory).relative_to(ROOT)
        # Installed dependencies and Git internals are not project-owned source.
        child_directories[:] = [
            name
            for name in child_directories
            if name not in {".git", ".tools", ".venv", "venv", "node_modules", "__pycache__"}
        ]
        for filename in files:
            relative = (relative_directory / filename).as_posix()
            category = (
                "kept_local_private_or_generated"
                if private_path(relative) or relative.startswith((".pytest_cache/", ".ruff_cache/"))
                else "project_files"
            )
            inventory[category] += 1
    report = {
        "reviewed_at": datetime.now(UTC).isoformat(),
        "head": git("rev-parse", "HEAD").decode().strip(),
        "candidate_files": len(candidates),
        "historical_commits": int(git("rev-list", "--all", "--count").decode()),
        "historical_blobs": blobs,
        "local_inventory": dict(inventory),
        "findings": findings,
        "historical_findings": history_findings,
        "broken_local_links": broken_links,
        "reviewed_sample": {
            "path": REVIEWED_FIXTURE,
            "kind": "nine-row synthetic test fixture",
            "sha256": hashlib.sha256((ROOT / REVIEWED_FIXTURE).read_bytes()).hexdigest(),
        },
        "scope": "Current publication candidates and all reachable Git blobs: credential signatures, exact known local credentials, private/generated paths and local Markdown links. Workspace private data inventoried but retained. Installed runtimes excluded. Not a guarantee against every secret or an automated image/OCR privacy audit.",
        "publication_blocked": bool(findings or history_findings or broken_links),
    }
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="artifacts/publication-security.json")
    arguments = parser.parse_args()
    result = audit()
    output = Path(arguments.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    raise SystemExit(1 if result["publication_blocked"] else 0)
