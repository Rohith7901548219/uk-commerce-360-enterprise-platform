"""Exercise CI-style checks using only publication candidates and installed dependencies."""

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from audit_publication import GIT, ROOT, audit


def remove_checkout(checkout):
    local = (ROOT / ".local").resolve()
    checkout = checkout.resolve()
    if not checkout.is_relative_to(local) or not checkout.name.startswith("publication-checkout-"):
        raise ValueError("Refusing to remove anything outside a generated QA checkout")

    def clear_readonly(function, path, exception):
        target = Path(path).resolve()
        if not target.is_relative_to(checkout):
            raise ValueError("Cleanup path escapes the generated checkout") from exception
        target.chmod(stat.S_IREAD | stat.S_IWRITE)
        function(path)

    shutil.rmtree(checkout, onexc=clear_readonly)


def run():
    review = audit()
    if review["publication_blocked"]:
        raise RuntimeError("Publication review must pass before a clean-checkout test")
    names = subprocess.check_output([GIT, "ls-files", "-z"], cwd=ROOT).decode().split("\0")
    names += (
        subprocess.check_output([GIT, "ls-files", "--others", "--exclude-standard", "-z"], cwd=ROOT)
        .decode()
        .split("\0")
    )
    local = (ROOT / ".local").resolve()
    if not local.is_relative_to(ROOT.resolve()):
        raise ValueError("Unexpected local scratch path")
    checkout = Path(tempfile.mkdtemp(prefix="publication-checkout-", dir=local)).resolve()
    if not checkout.is_relative_to(local):
        raise ValueError("Unexpected clean-checkout path")
    try:
        for name in sorted(set(names) - {""}):
            source, destination = (ROOT / name).resolve(), (checkout / name).resolve()
            if not source.is_relative_to(ROOT.resolve()) or not destination.is_relative_to(checkout):
                raise ValueError("Publication path escapes its source or destination")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
        assert not (checkout / ".env").exists()
        assert not (checkout / "artifacts").exists()
        assert not (checkout / "data/raw").exists()
        env = os.environ.copy()
        for name in (
            "DATABASE_URL",
            "CUSTOMER_HASH_KEY",
            "WRITE_API_TOKEN",
            "POSTGRES_PASSWORD",
            "GH_TOKEN",
            "GITHUB_TOKEN",
            "MLFLOW_TRACKING_URI",
            "SERVICE_DATABASE_URL",
            "SERVICE_KAFKA_BOOTSTRAP_SERVERS",
        ):
            env.pop(name, None)
        env["PYTHONPATH"] = str(checkout / "src")
        for args in (
            [GIT, "init", "--initial-branch=main"],
            [GIT, "add", "."],
            [
                GIT,
                "-c",
                "user.name=Clean checkout verification",
                "-c",
                "user.email=qa@example.invalid",
                "commit",
                "--quiet",
                "-m",
                "Temporary reviewed publication snapshot",
            ],
        ):
            subprocess.run(args, cwd=checkout, env=env, check=True, capture_output=True)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-m",
                "not services",
                "-p",
                "no:cacheprovider",
                "--junitxml=artifacts/tests.xml",
                "--tb=short",
            ],
            cwd=checkout,
            env=env,
            check=True,
        )
        subprocess.run([sys.executable, "scripts/audit_publication.py"], cwd=checkout, env=env, check=True)
        report = {
            "verified_at": datetime.now(UTC).isoformat(),
            "source_candidates": len(set(names) - {""}),
            "private_environment_present": False,
            "raw_data_present": False,
            "model_binaries_present": False,
            "private_credential_environment_removed": True,
            "pytest_exit_code": 0,
            "history_audit_exit_code": 0,
            "scope": "Isolated copy of reviewed candidates using existing locked dependencies; no private local files or services supplied; not a hosted GitHub Actions run",
        }
        (ROOT / "artifacts/publication-clean-checkout.json").write_text(json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
    finally:
        # Only this newly created, verified scratch checkout is removed; project files remain intact.
        if checkout.is_relative_to(local) and checkout.name.startswith("publication-checkout-"):
            remove_checkout(checkout)


if __name__ == "__main__":
    run()
