# Trustpilot Take-Home – dbt Project

dbt models that ingest raw Trustpilot review CSVs into DuckDB and build curated layers consumed by the API service.

## Setup

```bash
poetry --directory tp_data_project env use 3.13.7
poetry --directory tp_data_project install
```

The local dbt profile lives in `local_dbt_profiles/profiles.yml` and resolves DuckDB paths from environment variables:

- `TP_DBT_DEV_PATH` – defaults to `../data/dev.duckdb`
- `TP_DBT_PROD_PATH` – defaults to `../data/prod.duckdb`
- `TP_DBT_DEFAULT_TARGET` – fallback target for container usage (defaults to `prod`)

## Common Commands

```bash
poetry --directory tp_data_project run dbt seed                 # load csv seeds into DuckDB
poetry --directory tp_data_project run dbt build --target dev
poetry --directory tp_data_project run dbt build --target prod
poetry --directory tp_data_project run dbt test --target dev
```

From the repository root the Makefile mirrors these flows:

```bash
make install-data
make dbt-build                               # default target=dev
make DBT_TARGET=prod dbt-test
```

## Documentation

```bash
poetry --directory tp_data_project run dbt docs generate
poetry --directory tp_data_project run dbt docs serve --port 8001
```

Visit http://127.0.0.1:8001 to browse the model catalog and lineage graph.

## Linting

```bash
poetry --directory tp_data_project run sqlfluff lint models
poetry --directory tp_data_project run sqlfluff fix models
# or from the repository root
make data-lint
make data-fix

# via Docker with the baked image
make docker-data-lint
make docker-data-fix
```

## Container Workflow

```bash
make docker-data-build
make docker-data-shell                # disposable shell with dbt installed
make docker-data-login                # reusable container rooted at /app/tp_data_project
```

Override DuckDB paths at runtime:

```bash
TP_DBT_PROD_PATH=/mnt/shared/prod.duckdb make DBT_TARGET=prod dbt-build
```

## Future Modelling Roadmap

- Medallion architecture: bronze (raw ingests) → silver (clean, conformed) → gold (analytics data sets).
- Semantic layer defining business metrics exposed to the API or BI tools.
- Data quality tests for freshness, nulls, and referential integrity to support production SLAs.
