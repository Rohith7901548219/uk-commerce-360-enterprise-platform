import argparse
import json
import logging
import secrets
from pathlib import Path


def bootstrap():
    from commerce.config import settings

    settings()
    env = Path(".env")
    if not env.exists():
        content = Path(".env.example").read_text(encoding="utf-8")
        for key in ("WRITE_API_TOKEN", "CUSTOMER_HASH_KEY", "POSTGRES_PASSWORD"):
            content = content.replace(f"{key}=\n", f"{key}={secrets.token_hex(32)}\n")
        env.write_text(content, encoding="utf-8")
    settings.cache_clear()


def main():
    parser = argparse.ArgumentParser(description="UK Commerce 360 local automation")
    parser.add_argument(
        "command",
        choices=["bootstrap", "download", "pipeline", "train", "replay", "consumer", "init", "demo"],
    )
    parser.add_argument("--path", type=Path)
    parser.add_argument("--fixture", action="store_true")
    parser.add_argument(
        "--mirrored", action="store_true", help="Explicitly label a separately acquired UCI mirror"
    )
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    bootstrap()
    if args.command == "bootstrap":
        print("Workspace environment initialized; secrets are stored only in ignored .env")
    elif args.command in ("download", "pipeline", "demo"):
        from commerce.ingest import download_data, run_pipeline

        path = args.path or (Path("data/fixtures/retail.csv") if args.fixture else download_data())
        if args.command != "download":
            print(json.dumps(run_pipeline(path, fixture=args.fixture, mirrored=args.mirrored), indent=2))
        else:
            print(path)
        if args.command == "demo":
            from commerce.ml import train_all

            train_all()
    elif args.command == "init":
        from commerce.db import initialize

        initialize()
    elif args.command == "train":
        from commerce.ml import train_all

        train_all()
    else:
        from commerce.streaming import consume, produce_replay

        (consume if args.command == "consumer" else produce_replay)(limit=args.limit)


if __name__ == "__main__":
    main()
