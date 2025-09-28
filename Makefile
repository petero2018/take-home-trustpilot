POETRY ?= poetry
DOCKER ?= docker
API_ENV ?= prod
API_DUCKDB_PATH ?=
API_DUCKDB_SCHEMA ?=
API_DUCKDB_READ_ONLY ?= true
API_DB_BACKEND ?=
API_DB_POOL_SIZE ?=
API_DB_POOL_TIMEOUT ?=
API_LOG_LEVEL ?=
DBT_TARGET ?= dev
DBT_DOCS_PORT ?= 8001
DOCKER_REPOSITORY ?= python
DOCKER_DATA_IMAGE_NAME ?= take-home-data
DOCKER_API_IMAGE_NAME ?= take-home-api
PYTHON_VERSION ?= 3.13.7
PYTHON_FLAVOUR ?= slim
POETRY_VERSION ?= 2.2.1
GIT_VERSION := $(shell git -C . describe --tags 2> /dev/null || git -C . rev-parse --short HEAD)
DOCKER_DATA_IMAGE_TAG ?= $(PYTHON_VERSION)-$(GIT_VERSION)
DOCKER_DATA_IMAGE ?= $(DOCKER_REPOSITORY)/$(DOCKER_DATA_IMAGE_NAME):$(DOCKER_DATA_IMAGE_TAG)
DOCKER_API_IMAGE ?= $(DOCKER_REPOSITORY)/$(DOCKER_API_IMAGE_NAME):$(DOCKER_DATA_IMAGE_TAG)
TP_DBT_DEV_PATH ?= /app/data/dev.duckdb
TP_DBT_PROD_PATH ?= /app/data/prod.duckdb
TP_DBT_DEFAULT_TARGET ?= prod
.DEFAULT_GOAL := help
SHELL := bash

.PHONY: help install-api install-data api-serve api-test api-lint api-fix dbt-build dbt-test dbt-docs data-lint data-sqlfix docker-data-build docker-data-shell docker-data-login docker-data-lint docker-data-sqlfix docker-api-build docker-api-serve docker-api-shell docker-api-lint docker-api-fix

help:
	@echo "Available targets:"

	@echo "API project local virtual env targets:"

	@echo "  install-api            Install API project dependencies"
	@echo "  api-serve              Run FastAPI (override with API_ENV=dev, etc.)"
	@echo "  api-test               Run tp_api_project test suite"
	@echo "  api-lint               Run Black/Ruff/Mypy checks for tp_api_project"
	@echo "  api-fix                Auto-format imports & style for tp_api_project"

	@echo "Data project local virtual env targets:"

	@echo "  install-data           Install dbt project dependencies"
	@echo "  dbt-build              Run dbt build (override DBT_TARGET=prod)"
	@echo "  dbt-test               Run dbt test (override DBT_TARGET=prod)"
	@echo "  dbt-docs               Generate + serve dbt docs (DBT_DOCS_PORT=...)"
	@echo "  data-lint              Run SQLFluff linting for tp_data_project"
	@echo "  data-sqlfix            Auto-fix SQLFluff issues for tp_data_project"

	@echo "Data project docker container targets:"

	@echo "  docker-data-build      Build the dbt Docker image"
	@echo "  docker-data-shell      Run an interactive shell in the dbt image"
	@echo "  docker-data-login      Run/reuse a named dbt container"
	@echo "  docker-data-lint       Run SQLFluff inside the dbt Docker image"
	@echo "  docker-data-sqlfix     Auto-fix SQLFluff issues inside the dbt Docker image"

	@echo "API project docker container targets:"

	@echo "  docker-api-build       Build the API Docker image"
	@echo "  docker-api-serve       Run the API image (bind to port 8000)"
	@echo "  docker-api-shell       Run an interactive shell in the API image"
	@echo "  docker-api-lint        Run Black/Ruff/Mypy inside the API Docker image"
	@echo "  docker-api-fix         Auto-format using Docker image for tp_api_project"

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

api-test:
	$(POETRY) --directory tp_api_project run pytest

api-lint:
	$(POETRY) --directory tp_api_project run black --check app tests
	$(POETRY) --directory tp_api_project run ruff check
	$(POETRY) --directory tp_api_project run mypy app

api-fix:
	$(POETRY) --directory tp_api_project run black app tests
	$(POETRY) --directory tp_api_project run ruff check --fix

dbt-build:
	$(POETRY) --directory tp_data_project run dbt build --target $(DBT_TARGET)

dbt-test:
	$(POETRY) --directory tp_data_project run dbt test --target $(DBT_TARGET)

dbt-docs:
	$(POETRY) --directory tp_data_project run dbt docs generate
	$(POETRY) --directory tp_data_project run dbt docs serve --port $(DBT_DOCS_PORT)

data-lint:
	$(POETRY) --directory tp_data_project run sqlfluff lint models

data-sqlfix:
	$(POETRY) --directory tp_data_project run sqlfluff fix models

docker-data-build:
	@echo "Building data image $(DOCKER_DATA_IMAGE)"
	$(DOCKER) build \
		--file docker/data/Dockerfile \
		--tag $(DOCKER_DATA_IMAGE) \
		--build-arg DOCKER_REPOSITORY=$(DOCKER_REPOSITORY) \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg PYTHON_FLAVOUR=$(PYTHON_FLAVOUR) \
		--build-arg POETRY_VERSION=$(POETRY_VERSION) \
		.

docker-data-shell:
	@echo "Launching disposable dbt shell from $(DOCKER_DATA_IMAGE)"
	$(DOCKER) run --rm -it \
		-e TP_DBT_DEV_PATH=$(TP_DBT_DEV_PATH) \
		-e TP_DBT_PROD_PATH=$(TP_DBT_PROD_PATH) \
		-e TP_DBT_DEFAULT_TARGET=$(TP_DBT_DEFAULT_TARGET) \
		$(DOCKER_DATA_IMAGE) \
		bash

docker-data-login:
	@echo "Cleaning up existing container (if any)"
	-@$(DOCKER) rm -f tp_data_container >/dev/null 2>&1 || true
	@echo "Starting interactive container $(DOCKER_DATA_IMAGE)"
	$(DOCKER) run -it --name tp_data_container \
		-e TP_DBT_DEV_PATH=$(TP_DBT_DEV_PATH) \
		-e TP_DBT_PROD_PATH=$(TP_DBT_PROD_PATH) \
		-e TP_DBT_DEFAULT_TARGET=$(TP_DBT_DEFAULT_TARGET) \
		$(DOCKER_DATA_IMAGE) \
		bash -c "cd /app/tp_data_project && exec bash"

docker-data-lint: docker-data-build
	@echo "Running SQLFluff lint inside $(DOCKER_DATA_IMAGE)"
	$(DOCKER) run --rm \
		-e TP_DBT_DEV_PATH=$(TP_DBT_DEV_PATH) \
		-e TP_DBT_PROD_PATH=$(TP_DBT_PROD_PATH) \
		$(DOCKER_DATA_IMAGE) \
		poetry --directory tp_data_project run sqlfluff lint models

docker-data-sqlfix: docker-data-build
	@echo "Running SQLFluff fix inside $(DOCKER_DATA_IMAGE)"
	$(DOCKER) run --rm \
		-e TP_DBT_DEV_PATH=$(TP_DBT_DEV_PATH) \
		-e TP_DBT_PROD_PATH=$(TP_DBT_PROD_PATH) \
		$(DOCKER_DATA_IMAGE) \
		poetry --directory tp_data_project run sqlfluff fix models

docker-api-build:
	@echo "Building API image $(DOCKER_API_IMAGE)"
	$(DOCKER) build \
		--file docker/api/Dockerfile \
		--tag $(DOCKER_API_IMAGE) \
		--build-arg DOCKER_REPOSITORY=$(DOCKER_REPOSITORY) \
		--build-arg PYTHON_VERSION=$(PYTHON_VERSION) \
		--build-arg PYTHON_FLAVOUR=$(PYTHON_FLAVOUR) \
		--build-arg POETRY_VERSION=$(POETRY_VERSION) \
		.

docker-api-shell:
	@echo "Launching disposable API shell from $(DOCKER_API_IMAGE)"
	$(DOCKER) run --rm -it \
		-e TP_API_ENV=$(API_ENV) \
		-e TP_API_DUCKDB_PATH=$(if $(API_DUCKDB_PATH),$(API_DUCKDB_PATH),/app/data/prod.duckdb) \
		-e TP_API_DUCKDB_SCHEMA=$(API_DUCKDB_SCHEMA) \
		-e TP_API_DUCKDB_READ_ONLY=$(API_DUCKDB_READ_ONLY) \
		-e TP_API_DB_BACKEND=$(API_DB_BACKEND) \
		-e TP_API_DB_POOL_SIZE=$(API_DB_POOL_SIZE) \
		-e TP_API_DB_POOL_TIMEOUT=$(API_DB_POOL_TIMEOUT) \
		-e TP_API_LOG_LEVEL=$(API_LOG_LEVEL) \
		$(DOCKER_API_IMAGE) \
		bash

docker-api-lint: docker-api-build
	@echo "Running Black/Ruff/Mypy inside $(DOCKER_API_IMAGE)"
	$(DOCKER) run --rm \
		-e TP_API_ENV=$(API_ENV) \
		-e TP_API_DUCKDB_PATH=$(if $(API_DUCKDB_PATH),$(API_DUCKDB_PATH),/app/data/prod.duckdb) \
		-e TP_API_DUCKDB_SCHEMA=$(API_DUCKDB_SCHEMA) \
		-e TP_API_DUCKDB_READ_ONLY=$(API_DUCKDB_READ_ONLY) \
		-e TP_API_DB_BACKEND=$(API_DB_BACKEND) \
		-e TP_API_DB_POOL_SIZE=$(API_DB_POOL_SIZE) \
		-e TP_API_DB_POOL_TIMEOUT=$(API_DB_POOL_TIMEOUT) \
		-e TP_API_LOG_LEVEL=$(API_LOG_LEVEL) \
		$(DOCKER_API_IMAGE) \
		bash -c "poetry --directory tp_api_project run black --check app tests && poetry --directory tp_api_project run ruff check && poetry --directory tp_api_project run mypy app"

docker-api-fix: docker-api-build
	@echo "Running formatter fixes inside $(DOCKER_API_IMAGE)"
	$(DOCKER) run --rm \
		-e TP_API_ENV=$(API_ENV) \
		-e TP_API_DUCKDB_PATH=$(if $(API_DUCKDB_PATH),$(API_DUCKDB_PATH),/app/data/prod.duckdb) \
		-e TP_API_DUCKDB_SCHEMA=$(API_DUCKDB_SCHEMA) \
		-e TP_API_DUCKDB_READ_ONLY=$(API_DUCKDB_READ_ONLY) \
		-e TP_API_DB_BACKEND=$(API_DB_BACKEND) \
		-e TP_API_DB_POOL_SIZE=$(API_DB_POOL_SIZE) \
		-e TP_API_DB_POOL_TIMEOUT=$(API_DB_POOL_TIMEOUT) \
		-e TP_API_LOG_LEVEL=$(API_LOG_LEVEL) \
		$(DOCKER_API_IMAGE) \
		bash -c "poetry --directory tp_api_project run black app tests && poetry --directory tp_api_project run ruff check --fix"

docker-api-serve:
	@echo "Cleaning up existing API container (if any)"
	-@$(DOCKER) rm -f tp_api_container >/dev/null 2>&1 || true
	@echo "Starting API container $(DOCKER_API_IMAGE) on port 8000"
	$(DOCKER) run -it --name tp_api_container \
		-p 127.0.0.1:8000:8000 \
		-e TP_API_ENV=$(API_ENV) \
		-e TP_API_DUCKDB_PATH=$(if $(API_DUCKDB_PATH),$(API_DUCKDB_PATH),/app/data/prod.duckdb) \
		-e TP_API_DUCKDB_SCHEMA=$(API_DUCKDB_SCHEMA) \
		-e TP_API_DUCKDB_READ_ONLY=$(API_DUCKDB_READ_ONLY) \
		-e TP_API_DB_BACKEND=$(API_DB_BACKEND) \
		-e TP_API_DB_POOL_SIZE=$(API_DB_POOL_SIZE) \
		-e TP_API_DB_POOL_TIMEOUT=$(API_DB_POOL_TIMEOUT) \
		-e TP_API_LOG_LEVEL=$(API_LOG_LEVEL) \
		$(DOCKER_API_IMAGE)
