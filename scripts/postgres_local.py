"""Workspace-local PostgreSQL operations; no Windows service or administrator needed."""

import argparse
import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from dotenv import dotenv_values
from sqlalchemy import DateTime, create_engine, func, select

from commerce.db import insert_ignore, metadata

ROOT = Path(__file__).resolve().parents[1]
BIN = ROOT / ".tools/postgres-runtime/pgsql/bin"
CLUSTER = ROOT / ".local/pgdata"
PORT = 5433


def config():
    password = dotenv_values(ROOT / ".env").get("POSTGRES_PASSWORD")
    if not password:
        raise ValueError("Run commerce bootstrap first")
    return password


def start():
    password = config()
    if not (CLUSTER / "PG_VERSION").exists():
        secret_file = ROOT / ".local/pg-init-secret.tmp"
        secret_file.write_text(password, encoding="utf-8")
        try:
            subprocess.run(
                [
                    str(BIN / "initdb.exe"),
                    "-D",
                    str(CLUSTER),
                    "-U",
                    "commerce",
                    "--pwfile",
                    str(secret_file),
                    "-A",
                    "scram-sha-256",
                    "--encoding",
                    "UTF8",
                    "--locale",
                    "C",
                ],
                check=True,
            )
        finally:
            secret_file.unlink(missing_ok=True)
    running = subprocess.run([str(BIN / "pg_ctl.exe"), "-D", str(CLUSTER), "status"], capture_output=True)
    if running.returncode:
        subprocess.run(
            [
                str(BIN / "pg_ctl.exe"),
                "-D",
                str(CLUSTER),
                "-l",
                str(ROOT / ".local/postgres.log"),
                "-o",
                f"-h 127.0.0.1 -p {PORT}",
                "start",
                "-w",
            ],
            check=True,
        )
    with psycopg.connect(
        host="127.0.0.1", port=PORT, user="commerce", password=password, dbname="postgres", autocommit=True
    ) as connection:
        for database in ("commerce", "commerce_test"):
            if not connection.execute("select 1 from pg_database where datname=%s", (database,)).fetchone():
                connection.execute(
                    psycopg.sql.SQL("CREATE DATABASE {}").format(psycopg.sql.Identifier(database))
                )
    print(f"PostgreSQL verified on 127.0.0.1:{PORT}; secrets retained in ignored .env only")


def connection_url(database="commerce"):
    return f"postgresql+psycopg://commerce:{config()}@127.0.0.1:{PORT}/{database}"


def environment(database="commerce"):
    env = os.environ.copy()
    env.update({k: str(v) for k, v in dotenv_values(ROOT / ".env").items() if v is not None})
    env.update(
        DATABASE_URL=connection_url(database),
        POSTGRES_HOST="127.0.0.1",
        POSTGRES_PORT=str(PORT),
        POSTGRES_DB=database,
        SERVICE_DATABASE_URL=connection_url("commerce_test"),
        DBT_SEND_ANONYMOUS_USAGE_STATS="false",
    )
    return env


def transfer():
    """Copy validated local warehouse to the project's own PostgreSQL cluster, preserving lineage."""
    source = create_engine("sqlite:///" + str(ROOT / "data/warehouse/commerce.db"))
    destination = create_engine(connection_url())
    env = environment()
    subprocess.run([str(ROOT / ".venv/Scripts/alembic.exe"), "upgrade", "head"], env=env, check=True)
    counts = {}
    for table in metadata.sorted_tables:
        with source.connect() as reader, destination.connect() as writer:
            expected = reader.scalar(select(func.count()).select_from(table))
            existing = writer.scalar(select(func.count()).select_from(table))
        if existing > expected:
            raise ValueError(f"{table.name} contains extra rows; refusing to overwrite")
        if existing != expected:
            with source.connect() as reader:
                rows = reader.execute(select(table)).mappings()
                while batch := rows.fetchmany(2000):
                    records = [dict(x) for x in batch]
                    for record in records:
                        for column in table.columns:
                            value = record.get(column.name)
                            if (
                                isinstance(column.type, DateTime)
                                and value is not None
                                and value.tzinfo is None
                            ):
                                record[column.name] = value.replace(tzinfo=UTC)
                    with destination.begin() as writer:
                        insert_ignore(writer, table, records)
        with destination.connect() as writer:
            actual = writer.scalar(select(func.count()).select_from(table))
        if actual != expected:
            raise ValueError(f"Count mismatch for {table.name}: {actual} vs {expected}")
        counts[table.name] = actual
        print(f"{table.name}: {actual:,} reconciled", flush=True)
    Path("artifacts/postgres_transfer.json").write_text(
        json.dumps({"verified_at": datetime.now(UTC).isoformat(), "counts": counts}, indent=2)
    )
    source.dispose()
    destination.dispose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["start", "stop", "verify", "transfer", "dbt"])
    action = parser.parse_args().action
    if action == "start":
        start()
    elif action == "stop":
        running = subprocess.run([str(BIN / "pg_ctl.exe"), "-D", str(CLUSTER), "status"], capture_output=True)
        if running.returncode == 0:
            subprocess.run([str(BIN / "pg_ctl.exe"), "-D", str(CLUSTER), "stop", "-m", "fast"], check=True)
        else:
            print("Owned PostgreSQL cluster already stopped")
    elif action == "verify":
        subprocess.run(
            [
                str(ROOT / ".venv/Scripts/python.exe"),
                "-m",
                "pytest",
                "tests/test_services.py",
                "-k",
                "postgres",
                "-v",
                "-p",
                "no:cacheprovider",
                "--tb=short",
                "--junitxml=artifacts/postgres-tests.xml",
            ],
            env=environment("commerce_test"),
            check=True,
        )
    elif action == "dbt":
        subprocess.run(
            [str(ROOT / ".venv/Scripts/dbt.exe"), "build", "--project-dir", "dbt", "--profiles-dir", "dbt"],
            env=environment(),
            check=True,
        )
    else:
        transfer()
