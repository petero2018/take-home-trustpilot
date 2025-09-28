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

Treat the dbt project as the spine of the analytics platform. New data lands in bronze, is scrubbed and stitched together in silver, then graduates to gold once it carries business-ready facts and dimensions. A thin semantic layer on top tells the story in business language, powering BI dashboards and the FastAPI endpoints alike.

Trust is earned through documentation and guardrails. Automated freshness, uniqueness, and accepted-value tests catch drift before it hits downstream stakeholders. Rich column descriptions and dbt exposures spell out who depends on the certified `crt_tp_reviews` model, so the blast radius of a change is obvious in `dbt docs`.

The architecture already mirrors the warehouses we might adopt next. Materialisations line up with BigQuery/Snowflake best practices (surrogate keys, conformed dims, incremental logic), so scaling out is more about configuration than code rewrites. Late-arriving data handling and partition-friendly keys keep runtime predictable as volumes climb.

Quality stays high because we layer in unit tests, data contracts, and semantic-layer metric checks while SQLFluff keeps the codebase readable. When it’s time to trim runtime or spend, state-aware runs (`dbt build --select state:modified+`), off-peak scheduling, and archival jobs keep the warehouse bill honest.

## Technology and Deployment Considerations

In production the dbt code ships as a container. CI builds the image, runs `sqlfluff lint` and `dbt build --select state:modified+`, publishes docs artefacts, and pushes to Artifact Registry. Cloud Composer (Airflow) then pulls that image into a DAG so bronze→silver→gold becomes just another batch task with quality checks baked in. Separate repos keep API and data pipelines clean; Terraform wires secrets/env vars.

Observability is part of the pipeline: dbt run results land in Cloud Monitoring or BigQuery for trend analysis, and PagerDuty notifications fire when success rates dip. Exposures mean the API team knows immediately if their upstream model failed. Knowledge sharing keeps pace via gated `dbt docs`, architecture diagrams in git, and quick Loom walkthroughs. As maturity grows we integrate with a catalogue (e.g., DataHub) and schedule access reviews for PII-heavy models so compliance stays ahead of audits.

# Future API Project

## Architecture Considerations

The API matures into a layered service. The HTTP layer owns transport, a service layer encodes business rules, and persistence adapters know how to talk to DuckDB today and BigQuery tomorrow. That separation makes it painless to add caching (Redis, CDN-backed CSV downloads), better pagination (keyset over offset), or even new response formats (JSON, Parquet) without retooling the whole app.

Reliability is non-negotiable: we define SLOs (P95 <1s, <1% 5xx), add `/healthz/deep` checks that hit the database, and design graceful fallbacks like cached responses or Retry-After headers when the warehouse is busy. Security keeps pace via OAuth2/JWT, WAF and rate limiting, mTLS between services, and schema-level RBAC once the warehouse lives in BigQuery.

Performance and cost stay balanced by sticking with streaming CSV as the default but offering asynchronous exports for large pulls. We run on scale-to-zero platforms (Cloud Run) so idle time costs cents, and we benchmark pool sizing before scaling horizontally. CDN caching and Cloud Armor rules tame egress and DDoS risk.

Quality is enforced through contract tests (Schemathesis against the OpenAPI schema), integration tests with ephemeral DuckDB instances, and smoke tests in CI. FastAPI keeps consumer docs fresh via `/docs`, while ADRs capture the why behind choices like CSV-first or pool tuning so newcomers can come up to speed quickly.

## Technology and Deployment Considerations

- CI/CD stages: `make api-lint` (Black/Ruff/Mypy) → `make api-test` with coverage gates → build Docker image → vulnerability scan (GCP Artifact Analysis) → deploy to Cloud Run via CLI run within CI/CD process.
- Config management: centralise env vars in Secret Manager, inject via Cloud Run revisions, and attach workload identity so the API reads warehouse creds without long-lived keys.
- Monitoring & alerting: instrument with OpenTelemetry; export traces/metrics to Cloud Monitoring or Datadog; set alerts for latency spikes, pool exhaustion, and elevated 4xx/5xx rates.
- Documentation sharing: keep developer docs in MkDocs or README, rely on FastAPI’s `/docs` for consumers, and link runbooks/playbooks from alert notifications.
- Production hardening: rate limiting (API Gateway/Cloud Endpoints), automated DDoS protection, request/response payload logging with PII masking, and chaos drills to validate failover plans.
