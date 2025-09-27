POETRY ?= poetry
API_ENV ?= prod
API_DUCKDB_PATH ?=
API_DUCKDB_SCHEMA ?=
API_DUCKDB_READ_ONLY ?=
API_DB_BACKEND ?=
API_DB_POOL_SIZE ?=
API_DB_POOL_TIMEOUT ?=
API_LOG_LEVEL ?=
DBT_TARGET ?= dev

.PHONY: install-api install-data api-serve dbt-build dbt-test dbt-docs

install-api:
	$(POETRY) --directory tp_api_project install

install-data:
	$(POETRY) --directory tp_data_project install

api-serve: export TP_API_ENV=$(API_ENV)
api-serve: export TP_API_DUCKDB_PATH=$(API_DUCKDB_PATH)
api-serve: export TP_API_DUCKDB_SCHEMA=$(API_DUCKDB_SCHEMA)
api-serve: export TP_API_DUCKDB_READ_ONLY=$(API_DUCKDB_READ_ONLY)
api-serve: export TP_API_DB_BACKEND=$(API_DB_BACKEND)
api-serve: export TP_API_DB_POOL_SIZE=$(API_DB_POOL_SIZE)
api-serve: export TP_API_DB_POOL_TIMEOUT=$(API_DB_POOL_TIMEOUT)
api-serve: export TP_API_LOG_LEVEL=$(API_LOG_LEVEL)
api-serve:
	$(POETRY) --directory tp_api_project run uvicorn app.main:app --reload

dbt-build:
	$(POETRY) --directory tp_data_project run dbt build --target $(DBT_TARGET)

dbt-test:
	$(POETRY) --directory tp_data_project run dbt test --target $(DBT_TARGET)

dbt-docs:
	$(POETRY) --directory tp_data_project run dbt docs generate
	$(POETRY) --directory tp_data_project run dbt docs serve --port $(DBT_DOCS_PORT)
DBT_DOCS_PORT ?= 8001
