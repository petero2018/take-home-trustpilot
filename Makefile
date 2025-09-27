POETRY ?= poetry

.PHONY: install-api install-data api-serve dbt-run dbt-test

install-api:
	$(POETRY) --directory tp_api_project install

install-data:
	$(POETRY) --directory tp_data_project install

api-serve:
	$(POETRY) --directory tp_api_project run uvicorn app.main:app --reload

dbt-run:
	$(POETRY) --directory tp_data_project run dbt run

dbt-test:
	$(POETRY) --directory tp_data_project run dbt test
