# Trustpilot Take-Home Overview

This take-home delivers two cooperating services that expose Trustpilot review data:

- **[tp_api_project](tp_api_project/README.md)** – FastAPI application streaming DuckDB data as CSV.
- **[tp_data_project](tp_data_project/README.md)** – dbt project that models raw data into API-ready tables.

Both projects share the DuckDB file in `data/` and are containerised for easy CI/CD integration.

## How the brief is addressed

- **Data exposure** – `/reviews/by-business`, `/reviews/by-user`, and `/users/{user_id}` stream CSV directly from DuckDB so analysts and integrations can download results without an extra conversion step.
- **Error handling** – Domain exceptions (not found, data access failures, pool exhaustion) return structured JSON payloads with the right HTTP code (404/500/503) and log context for incident response.
- **Performance** – Query helpers stream results in batches to keep memory use flat, and a small DuckDB connection pool protects the database from thundering herds.
- **Data pipeline** – dbt models organise the dataset and can evolve toward a bronze/silver/gold medallion structure with a semantic layer for consumption.
- **Developer experience** – Poetry isolates dependencies per project; Makefile targets wrap common flows (`install`, `api-test`, `dbt-build`, Docker builds). Both services run locally with a copied `.env` and `make api-serve`.
- **Deployment readiness** – Separate Dockerfiles build slim API/dbt images. Environment variables line up with what a hosted DuckDB or warehouse (BigQuery) deployment would need.
- **Future hardening** – Authentication, WAF, private networking, and managed warehouse support are designed as incremental add-ons. Monitoring can piggyback on structured logs plus Cloud Monitoring/Datadog metrics and alerts.

## Quick start

1. Install `pyenv`, Python 3.13.7, and Poetry 1.8+.  
2. Follow project-specific setup in the linked READMEs.  
3. Use the Makefile helpers from the repo root:

   ```bash
   make install-api install-data
   make api-lint api-test
   make data-lint dbt-build
   make docker-api-serve
   ```

## Architecture at a glance

```text
          ┌────────────┐              ┌─────────────┐
          │ dbt models │  writes to   │             │
          │ (tp_data)  ├─────────────▶│  DuckDB     │
          └────────────┘              │  data file  │
                                       └─────┬──────┘
                                             │
                                             │ reads via connection pool
                                             ▼
                                   ┌────────────────────┐
                                   │ FastAPI service    │
                                   │ (tp_api)           │
                                   └────────┬───────────┘
                                            │
                               Streams CSV to clients
```

## Repository map

- `tp_api_project/` – FastAPI source, tests, Poetry files. See project README for details.
- `tp_data_project/` – dbt project, seeds, macros, profiles. See project README for details.
- `data/` – DuckDB files used by both projects.
- `docker/` – Dockerfiles for API and dbt images.
- `Makefile` – shortcuts for local development, testing, and container workflows.

