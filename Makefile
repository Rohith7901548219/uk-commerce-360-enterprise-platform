.PHONY: setup start test lint data train dbt
setup:
	uv sync --frozen --extra dev --extra warehouse
	uv run commerce bootstrap
start:
	docker compose up -d --build
test:
	uv run pytest -m 'not services'
lint:
	uv run ruff check .
data:
	uv run commerce pipeline
train:
	uv run commerce train
dbt:
	uv run dbt build --project-dir dbt --profiles-dir dbt
