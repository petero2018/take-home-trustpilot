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


# Future Data Project

## Architecture Considerations

This data project can be extended using a bronze–silver–gold layering approach, which is a common best practice for structuring modern data platforms.
	•	Bronze Layer (Landing)
The bronze layer is the raw landing zone where ingested data is first stored. At this stage, only basic data type conversions are applied. No business or technical transformations take place here. Instead, the focus is on:
	•	Ensuring proper data types.
	•	Applying fundamental quality checks (e.g., non-null enforcement).
	•	Preserving the original fidelity of ingested data.
In this PoC, we handled this layer with dbt seeds. In production, data ingestion into the bronze layer would typically occur through batch ingestion, streaming pipelines, or other ingestion services.
	•	Silver Layer (Refinement)
The silver layer is where technical transformations are applied to make the data usable for downstream modeling. This includes:
	•	Deduplication.
	•	Normalization and denormalization.
	•	Identity management.
	•	Unions and joins.
In this layer, the data is standardized and technically prepared for business consumption.
	•	Gold Layer (Business Models)
The gold layer contains business-facing models, primarily fact and dimension tables.
	•	Dimension tables: contain reference data, often designed as slowly changing dimensions with unique keys.
	•	Fact tables: contain event or transaction-level data, typically high-volume, keyed for efficient joins with dimensions.
	•	Both fact and dimension tables often include “current flags” to indicate the active record in a given context, while still enabling historical analysis.
	•	Semantic Layer (Optional, as maturity grows)
As organizational data maturity increases, a semantic layer can be introduced on top of the gold layer. This layer encapsulates additional business logic on metrics and semantics, further reinforcing the “single source of truth” concept.
Data from the semantic or gold layer can be:
	•	Exposed to BI or analytics tools.
	•	Served through APIs (e.g., the FastAPI solution in this project).
	•	Distributed to external applications via reverse ETL tools or processes.

## Technology and Deployment Considerations

At present, the dbt project is written so that it can be run either with or without tests. Looking ahead, the project can be extended with CI/CD practices to ensure reliable, cost-efficient, and standards-compliant deployments.
	•	Separation of Projects
As noted earlier, the data project and API project are best maintained in separate repositories. This separation makes it easier to design focused CI/CD pipelines for each.
	•	Deployment Flow
The dbt project can be deployed by running a single dbt build, which executes all models along with their associated tests. In CI/CD pipelines, this can be optimized further:
	•	Selective model execution: generate a manifest file from production, and in CI/CD only run models that have changed (--defer and --select state:modified).
	•	This ensures that only the relevant models are rebuilt and tested, reducing runtime and cost.
	•	Testing in CI/CD
	•	Pre-materialization checks: run SQLFluff with the agreed configuration to enforce SQL style and dbt coding standards.
	•	Post-materialization checks: run dbt test or dbt build on the changed models to validate integration and data quality after materialization.
	•	Environments and Targets
CI/CD pipelines can manage dbt targets (e.g. dev, prod) to control where data is materialized.
	•	Local development can materialize to a development schema.
	•	Production materialization should use a dedicated operational schema.
	•	In production, DuckDB will be replaced by a warehouse engine such as Google BigQuery (or an equivalent supported by dbt).


# Future API Project


## Architecture Considerations


## Technology and Deployment Considerations

As noted previously, keeping the API project in a separate repository allows CI/CD pipelines to be managed much more efficiently than in a single monorepo.


	•	CI/CD Pipeline Flow
      1.	Linting & Style Checks
         •	Run code linting tools (e.g. Black, Ruff) and any additional configured checks.
         •	Ensures that all changes adhere to repository standards and coding conventions.
      2.	Unit Tests with Coverage
         •	Execute the unit test suite, including tests with mock data for API endpoints.
         •	Enforce a minimum coverage threshold to ensure that pull requests are adequately tested.
      3.	Containerization
         •	Build the application into a Docker container if all linting and tests succeed.
         •	The container provides a consistent runtime environment across environments.
      4.	Deployment
         •	Deploy the container to a cloud hosting service such as Google Cloud Run.
         •	Containers can be stored and versioned in Google Container Registry (GCR) or Artifact Registry.
         •	This provides a straightforward path from tested code to production API deployment.
	•	Security, Monitoring, and Alerting
      •	Google Cloud provides built-in services for security scans of containers before deployment.
      •	Monitoring and alerting can be configured through GCP’s native tooling (e.g. Cloud Monitoring, Cloud Logging).
      •	These services enable visibility into API health, performance, and error rates.