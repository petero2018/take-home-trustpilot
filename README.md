# take-home-trustpilot

This repository contains two Python entry points that both read from the same DuckDB file in `data/`:

- `tp_api_project/` – FastAPI service that exposes review data from DuckDB
- `tp_data_project/` – dbt project that builds the DuckDB datasets consumed by the API

Each project now has its own Poetry environment so their dependency graphs stay isolated while the DuckDB database can be shared across them.

## Prerequisites

- [`pyenv`](https://github.com/pyenv/pyenv) with the build dependencies for your OS
- Python `3.13.7` installed via `pyenv`
- [Poetry](https://python-poetry.org/) 1.8+ (for `package-mode` and workspace support)
- DuckDB database present at `data/prod.duckdb` (or point `DUCKDB_PATH` to another file)

### Install Python 3.13.7 with pyenv

Use `pyenv` to make the required interpreter available:

```bash
pyenv versions
pyenv install -l
pyenv install 3.13.7
pyenv local 3.13.7
```

Verify the selected interpreter:

```bash
which python
python --version
```

## Setting up Poetry environments

Poetry is configured per sub-project. After ensuring the `pyenv` version is active, point each project at Python 3.13.7 and install dependencies:

```bash
poetry --directory tp_api_project env use 3.13.7
poetry --directory tp_api_project install

poetry --directory tp_data_project env use 3.13.7
poetry --directory tp_data_project install
```

Inspect the virtual environments if needed:

```bash
poetry --directory tp_api_project env list --full-path
poetry --directory tp_data_project env list --full-path
```

### Configure FastAPI settings

Copy the example environment file and adjust it for your setup:

```bash
cp tp_api_project/.env.example tp_api_project/.env
```

Key variables:

- `TP_API_ENV` – `prod` (default) or `dev`; toggles defaults for other settings.
- `TP_API_DUCKDB_PATH` – explicit path to the DuckDB database.
- `TP_API_DUCKDB_READ_ONLY` – `true|false`; defaults to `true` when `TP_API_ENV=prod`.
- `TP_API_DUCKDB_SCHEMA` – optional explicit schema; omit to auto-detect.

The legacy `DUCKDB_PATH` variable is also honoured for compatibility.

By default the service connects to `../data/prod.duckdb` in read-only mode. If no schema is
provided it will auto-detect where the tables live. Set `TP_API_ENV=dev` (and optionally
`TP_API_DUCKDB_PATH` or `TP_API_DUCKDB_SCHEMA`) if you want to work with a development
database instead.

### API project

Activate an environment for interactive use:

```bash
eval $(poetry --directory tp_api_project env activate)
which python
```

```bash
poetry --directory tp_api_project run uvicorn app.main:app --reload
```

Environment variables:

- `TP_API_ENV`, `TP_API_DUCKDB_PATH`, `TP_API_DUCKDB_READ_ONLY` (see above) control runtime configuration.
- `DUCKDB_PATH` remains a supported override for `TP_API_DUCKDB_PATH` if you prefer the older name.

#### Documentation

- Swagger UI: `http://127.0.0.1:8000/docs`
- OpenAPI JSON: `http://127.0.0.1:8000/openapi.json`

#### Example requests

With the server running locally on `http://127.0.0.1:8000`:

```bash
curl -s "http://127.0.0.1:8000/healthz"

# Provide reviews for business X
curl -s "http://127.0.0.1:8000/reviews/by-business?business_id=<BUSINESS_ID>" -o tp_api_project/tests/data/business.csv

# Provide reviews by user Y
curl -s "http://127.0.0.1:8000/reviews/by-user?user_id=<USER_ID>" -o tp_api_project/tests/data/user_reviews.csv

# Provide user account information for user Z
curl -s "http://127.0.0.1:8000/users/<USER_ID>" -o tp_api_project/tests/data/user_info.csv
```

Run tests:

```bash
poetry --directory tp_api_project run pytest
```

### Data project

Execute dbt commands through the project environment, e.g.:

```bash
poetry --directory tp_data_project run dbt seed   # ingest the CSV into DuckDB
poetry --directory tp_data_project run dbt build  # transform / model if needed
poetry --directory tp_data_project run dbt test
```

Generate interactive dbt docs:

```bash
poetry --directory tp_data_project run dbt docs generate
poetry --directory tp_data_project run dbt docs serve  # visit http://127.0.0.1:8000 to browse
```

The dbt project reads and writes tables inside the same DuckDB file referenced by the API.

## Makefile helpers

A lightweight `Makefile` wraps the most common commands:

```bash
make install-api   # poetry install inside tp_api_project
make install-data  # poetry install inside tp_data_project
make api-serve     # start the FastAPI app via uvicorn
make dbt-run       # dbt run inside tp_data_project
make dbt-test      # dbt test inside tp_data_project
```

These targets assume `poetry` is on your PATH.

## DuckDB storage

Both applications expect the DuckDB database at `data/prod.duckdb`. You can relocate the file and point to it with `DUCKDB_PATH`. Because each Poetry environment is independent, only the database file itself is shared.
