from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    database_url: str = "sqlite:///data/warehouse/commerce.db"
    api_base_url: str = "http://127.0.0.1:8000"
    kafka_bootstrap_servers: str = "127.0.0.1:19092"
    kafka_topic: str = "retail.transactions.v1"
    kafka_group: str = "commerce-warehouse-v1"
    write_api_token: str = ""
    customer_hash_key: str = ""
    mlflow_tracking_uri: str = "sqlite:///artifacts/mlflow.db"


@lru_cache
def settings() -> Settings:
    for directory in ("data/raw", "data/warehouse", "data/processed", "artifacts", ".local"):
        Path(directory).mkdir(parents=True, exist_ok=True)
    return Settings()
