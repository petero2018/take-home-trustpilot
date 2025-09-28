# Trustpilot Take-Home – API Service

FastAPI application that serves Trustpilot review data from DuckDB as streaming CSV downloads.

## Setup

This section and beyond assumes that your CLI terminal is currently active in the root directory of this project

```bash
poetry --directory tp_api_project env use 3.13.7
poetry --directory tp_api_project install
cp tp_api_project/.env.example tp_api_project/.env # change this as per your environment needs
```

### Key environment variables

- `TP_API_ENV` – `prod` (default) or `dev`; controls default DuckDB path, read-only flag, and logging.
- `TP_API_DUCKDB_PATH` / `DUCKDB_PATH` – overrides the location of the DuckDB file (defaults to `../data/prod.duckdb`).
- `TP_API_DUCKDB_READ_ONLY` – enable writes for dev flows; defaults to `true` in prod.
- `TP_API_DUCKDB_SCHEMA` – set the schema explicitly; omit to auto-detect.
- `TP_API_DB_POOL_SIZE` / `TP_API_DB_POOL_TIMEOUT` – DuckDB connection pool tuning knobs.
- `TP_API_LOG_LEVEL` – standard Python log level string.

## Running the API

```bash
poetry --directory tp_api_project run uvicorn app.main:app --reload
```

Swagger UI: http://127.0.0.1:8000/docs  
OpenAPI JSON: http://127.0.0.1:8000/openapi.json

Example requests to supported endpoints:

```bash
curl -s "http://127.0.0.1:8000/healthz"
curl -s "http://127.0.0.1:8000/reviews/by-business?business_id=<BUSINESS_ID>" -o tests/data/business.csv
curl -s "http://127.0.0.1:8000/reviews/by-user?user_id=<USER_ID>" -o tests/data/user_reviews.csv
curl -s "http://127.0.0.1:8000/users/<USER_ID>" -o tests/data/user_info.csv
```

Responses stream as `text/csv` per requirements; 404 and 5xx errors return a structured JSON payload (`detail` + `context`).

## Testing

```bash
poetry --directory tp_api_project run pytest
# or via Makefile from repo root
make api-test
```

## Linting

```bash
poetry --directory tp_api_project run black --check app tests
poetry --directory tp_api_project run ruff check
poetry --directory tp_api_project run mypy app
# or from repo root
make api-lint

# auto-format / import tidy
poetry --directory tp_api_project run black app tests
poetry --directory tp_api_project run ruff check --fix
make api-fix

# via Docker image
make docker-api-lint
make docker-api-fix
```

## Docker

```bash
make docker-api-build
make docker-api-serve
make API_ENV=dev API_DUCKDB_PATH=/app/data/dev.duckdb docker-api-serve
```

`docker-api-shell` opens an interactive shell inside the image with all environment variables respected.

## Observability Notes

- Structured logging with request context helps trace upstream issues.
- Health checks: `/healthz` returns `{ "status": "ok" }` and doubles as the baseline for uptime monitoring.
- Connection pool exhaustion surfaces as HTTP 503 with actionable messaging, easing alerting hooks.
