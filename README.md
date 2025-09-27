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
- `TP_API_DB_BACKEND` – database adapter (currently `duckdb` only, defaults to `duckdb`).
- `TP_API_DB_POOL_SIZE` – number of DuckDB connections kept in the pool (default `5`).
- `TP_API_DB_POOL_TIMEOUT` – seconds to wait for a pooled connection before timing out (default `5.0`).
- `TP_API_LOG_LEVEL` – optional Python logging level (e.g. `DEBUG`, `INFO`).

The legacy `DUCKDB_PATH` variable is also honoured for compatibility.

By default the service connects to `../data/prod.duckdb` in read-only mode and manages a
small DuckDB connection pool. If no schema is provided it will auto-detect where the tables
live. Set `TP_API_ENV=dev` (and optionally `TP_API_DUCKDB_PATH`, `TP_API_DUCKDB_SCHEMA`, or
pool settings) if you want to work with a development database instead.

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
- `TP_API_DB_BACKEND` – database adapter (currently `duckdb` only, defaults to `duckdb`).
- `TP_API_DB_POOL_SIZE` – number of DuckDB connections kept in the pool (default `5`).
- `TP_API_DB_POOL_TIMEOUT` – seconds to wait for a pooled connection before timing out (default `5.0`).
- `TP_API_LOG_LEVEL` – optional Python logging level (e.g. `DEBUG`, `INFO`).
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

The Makefile helpers let you switch API environments without editing code:

```bash
make api-serve                                    # serve using prod defaults
make API_ENV=dev API_DUCKDB_PATH=../data/dev.duckdb API_DUCKDB_READ_ONLY=false api-serve
make API_ENV=prod API_DUCKDB_PATH=../data/prod.duckdb api-serve
```

### Data project

Execute dbt commands through the project environment, e.g.:

```bash
poetry --directory tp_data_project run dbt seed   # ingest the CSV into DuckDB
poetry --directory tp_data_project run dbt build --target dev
poetry --directory tp_data_project run dbt build --target prod
poetry --directory tp_data_project run dbt test --target dev
```

Set `--target prod` (or any profile target defined in `profiles.yml`) to run against a
different environment. The Makefile mirrors this behaviour via the `DBT_TARGET` variable:

```bash
make dbt-build                    # default target is 'dev'
make DBT_TARGET=prod dbt-build     # run dbt build against prod
make DBT_TARGET=prod dbt-test
```

Generate interactive dbt docs:

```bash
poetry --directory tp_data_project run dbt docs generate
poetry --directory tp_data_project run dbt docs serve --port 8001  # visit http://127.0.0.1:8001
```

The dbt profile (in `tp_data_project/local_dbt_profiles/profiles.yml`) now resolves DuckDB
paths from environment variables, defaulting to `../data/*.duckdb`. If you store the
database elsewhere, export `TP_DBT_DEV_PATH` / `TP_DBT_PROD_PATH` before invoking dbt or
override them in the Makefile call, e.g.:

```bash
TP_DBT_PROD_PATH=/mnt/shared/prod.duckdb make DBT_TARGET=prod dbt-build
```

The dbt project reads and writes tables inside the same DuckDB file referenced by the API.

## Makefile helpers

A lightweight `Makefile` wraps the most common commands:

```bash
make install-api   # poetry install inside tp_api_project
make install-data  # poetry install inside tp_data_project
make api-serve     # start the FastAPI app via uvicorn (defaults to prod)
make dbt-build     # dbt build inside tp_data_project (target=dev by default)
make dbt-test      # dbt test inside tp_data_project (target=dev by default)
make dbt-docs      # generate + serve dbt docs (defaults to port 8001)
make docker-data-build  # build the dbt container image
make docker-data-login  # run the dbt image and cd into /app/tp_data_project
make docker-data-shell  # drop into a shell inside the freshly built image
make docker-api-build   # build the FastAPI container image
make docker-api-serve   # run the FastAPI image, binding to localhost:8000
make docker-api-shell   # drop into a shell inside the FastAPI image
```

These targets assume `poetry` is on your PATH.

### Docker images

Build the dbt image (defaults shown in the Makefile):

```bash
make docker-data-build
make DOCKER_REPOSITORY=ghcr.io/me \
     DOCKER_DATA_IMAGE_NAME=tp-data \
     DOCKER_DATA_IMAGE_TAG=latest \
     PYTHON_VERSION=3.13.7 \
     PYTHON_FLAVOUR=slim \
     docker-data-build

# Explore the container with environment overrides if needed
TP_DBT_PROD_PATH=/mnt/shared/prod.duckdb make docker-data-shell
# Clean and reuse a named container that drops you into /app/tp_data_project
make docker-data-login

# Example of running a one-off dbt command within the container via login target
make docker-data-login DBT_TARGET=prod
docker exec -it tp_data_container poetry --directory tp_data_project run dbt test --target prod
docker stop tp_data_container

# Build and run the API image
make docker-api-build
make docker-api-serve                          # binds to localhost:8000
make API_ENV=dev API_DUCKDB_PATH=/app/data/dev.duckdb docker-api-serve
make docker-api-shell                          # drop into the API container for debugging
```

The build context must be the repository root (the Makefile enforces this). Update
`TP_DBT_DEV_PATH` / `TP_DBT_PROD_PATH` when running containers so the dbt profile resolves
the correct DuckDB files. Similar environment overrides apply when composing for
production. The API container honours the same environment variables documented above;
override `API_ENV`, `API_DUCKDB_PATH`, or others on the `make docker-api-serve` command to
point at alternative DuckDB locations.

## DuckDB storage

Both applications expect the DuckDB database at `data/prod.duckdb`. You can relocate the file and point to it with `DUCKDB_PATH`. Because each Poetry environment is independent, only the database file itself is shared.
