.PHONY: help

define GET_MAKEFILE_DIR
$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))) | sed 's:/*$$::')
endef

MAKEFILE_DIR := $(GET_MAKEFILE_DIR)
export DAGSTER_HOME := $(MAKEFILE_DIR)/.dagster_home
export AIRFLOW_HOME := $(MAKEFILE_DIR)/.airflow_home
export DBT_PROJECT_DIR := $(MAKEFILE_DIR)/tutorial_example/shared/dbt
export DBT_PROFILES_DIR := $(MAKEFILE_DIR)/tutorial_example/shared/dbt
export DAGSTER_URL := http://localhost:3333

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dbt_setup: ## Initialize dbt project
	dbt seed

dev_install:
	pip install uv && \
	uv pip install -e ../../../dagster-airlift
	uv pip install -e .

# make airflow home and dagster home directories within current directory, set up env vars, and then
# set up airflow environment.
setup_local_env:
	make wipe && \
	mkdir -p $$AIRFLOW_HOME && \
	mkdir -p $$DAGSTER_HOME && \
	chmod +x ../../airflow_setup.sh && \
	../../airflow_setup.sh $(MAKEFILE_DIR)/tutorial_example/airflow_dags && \
	make dbt_setup

run_airflow:
	airflow standalone

run_dagster_dev:
	dagster dev -m tutorial_example.dagster_defs -p 3333

wipe: ## Wipe out all the files created by the Makefile
	rm -rf $$AIRFLOW_HOME $$DAGSTER_HOME

wipe_dagster: ## Wipe out all the files created by the Makefile
	rm -rf $$DAGSTER_HOME
