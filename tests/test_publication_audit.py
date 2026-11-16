import json
import shutil
import subprocess
from pathlib import Path

from scripts import audit_publication


def repository(tmp_path, monkeypatch):
    command = shutil.which("git") or "C:/Program Files/Git/cmd/git.exe"

    def git(*args):
        return subprocess.run([command, *args], cwd=tmp_path, check=True, capture_output=True)

    git("init")
    git("config", "user.name", "Publication audit test")
    git("config", "user.email", "test@example.invalid")
    fixture = tmp_path / "data/fixtures/retail.csv"
    fixture.parent.mkdir(parents=True)
    shutil.copyfile(Path("data/fixtures/retail.csv"), fixture)
    (tmp_path / ".gitignore").write_text(".env\n")
    monkeypatch.setattr(audit_publication, "ROOT", tmp_path)
    monkeypatch.setattr(audit_publication, "GIT", command)
    return git


def test_removed_historical_credential_still_blocks_publication(tmp_path, monkeypatch):
    git = repository(tmp_path, monkeypatch)
    token = "ghp_" + "A" * 36  # Synthetic signature, never an actual account credential.
    file = tmp_path / "configuration.txt"
    file.write_text(token)
    git("add", ".")
    git("commit", "-m", "Initial test history")
    file.write_text("No credential in the current file")
    git("add", ".")
    git("commit", "-m", "Remove synthetic credential from current version")
    report = audit_publication.audit()
    assert report["publication_blocked"] is True
    assert any(item["rule"] == "github_token" for item in report["historical_findings"])
    assert token not in json.dumps(report)


def test_ignored_private_config_is_retained_and_safe_sample_is_allowed(tmp_path, monkeypatch):
    git = repository(tmp_path, monkeypatch)
    secret = "synthetic-local-test-password"
    private = tmp_path / ".env"
    private.write_text("POSTGRES_PASSWORD=" + secret)
    git("add", ".")
    git("commit", "-m", "Only reviewed source and fixture")
    report = audit_publication.audit()
    assert report["publication_blocked"] is False
    assert report["historical_commits"] == 1
    assert private.read_text().endswith(secret)
    assert secret not in json.dumps(report)
