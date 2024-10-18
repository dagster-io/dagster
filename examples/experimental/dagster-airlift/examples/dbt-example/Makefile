.PHONY: help

define GET_MAKEFILE_DIR
$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))) | sed 's:/*$$::')
endef

export MAKEFILE_DIR := $(GET_MAKEFILE_DIR)
export DAGSTER_HOME := $(MAKEFILE_DIR)/.dagster_home
export AIRFLOW_HOME := $(MAKEFILE_DIR)/.airflow_home
export DBT_PROJECT_DIR := $(MAKEFILE_DIR)/dbt_example/shared/dbt
export DBT_PROFILES_DIR := $(MAKEFILE_DIR)/dbt_example/shared/dbt
export DAGSTER_URL := http://localhost:3333

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dbt_setup: ## Initialize dbt project
	dbt seed

dev_install:
	pip install uv && \
	uv pip install -e ../../../dagster-airlift
	uv pip install -e .

setup_local_env: 
	$(MAKE) wipe
	mkdir -p $(AIRFLOW_HOME)
	mkdir -p $(DAGSTER_HOME)
	chmod +x ../../scripts/airflow_setup.sh
	../../scripts/airflow_setup.sh $(MAKEFILE_DIR)/dbt_example/airflow_dags
	$(MAKE) dbt_setup

not_proxied:
	chmod +x ../../scripts/find_and_replace_in_yaml_dir.sh
	../../scripts/find_and_replace_in_yaml_dir.sh $(MAKEFILE_DIR)/dbt_example/airflow_dags/proxied_state True False

proxied: 
	chmod +x ../../scripts/find_and_replace_in_yaml_dir.sh
	../../scripts/find_and_replace_in_yaml_dir.sh $(MAKEFILE_DIR)/dbt_example/airflow_dags/proxied_state False True

run_airflow:
	airflow standalone

run_peer:
	dagster dev -m dbt_example.dagster_defs.peer -p 3333

run_observe: not_proxied
	dagster dev -m dbt_example.dagster_defs.observe -p 3333

run_migrate: proxied
	dagster dev -m dbt_example.dagster_defs.migrate -p 3333

run_complete:
	dagster dev -m dbt_example.dagster_defs.complete -p 3333

wipe: ## Wipe out all the files created by the Makefile
	rm -rf $(AIRFLOW_HOME) $(DAGSTER_HOME)

wipe_dagster: ## Wipe out all the files created by the Makefile
	rm -rf $$DAGSTER_HOME