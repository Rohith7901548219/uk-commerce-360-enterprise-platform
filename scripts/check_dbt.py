import os

from dbt.cli.main import dbtRunner

from commerce.config import settings

if __name__ == "__main__":
    # The profile password is supplied through the process environment, never an argument.
    from dotenv import load_dotenv

    load_dotenv()
    settings()
    os.environ.setdefault("DBT_SEND_ANONYMOUS_USAGE_STATS", "false")
    result = dbtRunner().invoke(["parse", "--project-dir", "dbt", "--profiles-dir", "dbt"])
    if not result.success:
        raise SystemExit(1)
