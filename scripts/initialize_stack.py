"""Container init job; mirror acquisition is an explicit deployment choice."""

import os
import subprocess
from pathlib import Path

from alembic import command
from alembic.config import Config

from commerce.ingest import download_data, run_pipeline
from commerce.ml import train_all

if __name__ == "__main__":
    command.upgrade(Config("alembic.ini"), "head")
    method = os.environ.get("DATA_ACQUISITION", "official")
    if method == "mirror":
        from acquire_mirror import acquire

        run_pipeline(acquire(), mirrored=True)
    elif method == "official":
        run_pipeline(download_data())
    else:
        raise ValueError("DATA_ACQUISITION must be official or mirror")
    subprocess.run(["dbt", "build", "--project-dir", "dbt", "--profiles-dir", "dbt"], check=True)
    train_all()
    if not Path("artifacts/repurchase.joblib").exists():
        raise RuntimeError("Model serving artifact was not created")
