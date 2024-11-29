.PHONY: help

define GET_MAKEFILE_DIR
$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))) | sed 's:/*$$::')
endef

export MAKEFILE_DIR := $(GET_MAKEFILE_DIR)
export DAGSTER_HOME := $(MAKEFILE_DIR)/.dagster_home
export AIRFLOW_HOME := $(MAKEFILE_DIR)/.airflow_home
export CUSTOMERS_DBT_PROJECT_DIR := $(MAKEFILE_DIR)/airflow-codebase/customers-dbt
export CUSTOMERS_DBT_PROFILES_DIR := $(MAKEFILE_DIR)/airflow-codebase/customers-dbt
export ORDERS_DBT_PROJECT_DIR := $(MAKEFILE_DIR)/airflow-codebase/orders-dbt
export ORDERS_DBT_PROFILES_DIR := $(MAKEFILE_DIR)/airflow-codebase/orders-dbt
export SDF_PROJECT_DIR := $(MAKEFILE_DIR)/dagster-codebase/sdf-project
export DAGSTER_URL := http://localhost:3333
export AIRLIFT_MODULE_DIR := $(MAKEFILE_DIR)/../../python_modules/libraries/dagster-airlift

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dbt_setup: ## Initialize dbt project
	DBT_PROJECT_DIR=$(CUSTOMERS_DBT_PROJECT_DIR) dbt seed --profiles-dir $(CUSTOMERS_DBT_PROFILES_DIR)
	DBT_PROJECT_DIR=$(ORDERS_DBT_PROJECT_DIR) dbt seed --profiles-dir $(ORDERS_DBT_PROFILES_DIR)

sdf_setup:
	sdf compile $(SDF_PROJECT_DIR)

dev_install:
	pip install uv && \
	uv pip install -e $(AIRLIFT_MODULE_DIR)[tutorial]
	uv pip install -e $(MAKEFILE_DIR)/airflow-codebase
	uv pip install -e $(MAKEFILE_DIR)/dagster-codebase/sdf-location
	uv pip install -e $(MAKEFILE_DIR)/dagster-codebase/scraping-location
	uv pip install -e $(MAKEFILE_DIR)/dagster-codebase/adhoc-location

setup_local_env: dev_install dbt_setup sdf_setup ## Setup the local environment
	$(MAKE) wipe
	mkdir -p $(AIRFLOW_HOME)
	mkdir -p $(DAGSTER_HOME)
	chmod +x $(MAKEFILE_DIR)/airflow_setup.sh
	AIRFLOW_HOME=$(AIRFLOW_HOME) $(MAKEFILE_DIR)/airflow_setup.sh $(MAKEFILE_DIR)/airflow-codebase/airflow_dags 

run_airflow:
	AIRFLOW_HOME=$(AIRFLOW_HOME) airflow standalone

run_dagster:
	dagster dev -w $(MAKEFILE_DIR)/dagster-codebase/workspace.yaml -p 3333

wipe: ## Wipe out all the files created by the Makefile
	rm -rf $(AIRFLOW_HOME) $(DAGSTER_HOME)

wipe_dagster: ## Wipe out all the files created by the Makefile
	rm -rf $$DAGSTER_HOME