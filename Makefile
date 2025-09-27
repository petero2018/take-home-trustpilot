POETRY ?= poetry
DBT_TARGET ?= dev

.PHONY: install-api install-data api-serve dbt-build dbt-test

install-api:
	$(POETRY) --directory tp_api_project install

install-data:
	$(POETRY) --directory tp_data_project install

api-serve:
	$(POETRY) --directory tp_api_project run uvicorn app.main:app --reload

dbt-build:
	$(POETRY) --directory tp_data_project run dbt build --target $(DBT_TARGET)

dbt-test:
	$(POETRY) --directory tp_data_project run dbt test --target $(DBT_TARGET)
