.PHONY: help

define GET_MAKEFILE_DIR
$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))) | sed 's:/*$$::')
endef

export MAKEFILE_DIR := $(GET_MAKEFILE_DIR)
export DAGSTER_HOME := $(MAKEFILE_DIR)/.dagster_home
export AIRFLOW_HOME := $(MAKEFILE_DIR)/.airflow_home
export DAGSTER_URL := http://localhost:3333
export AIRLIFT_MODULE_DIR := $(MAKEFILE_DIR)/..

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev_install:
	pip install uv
	uv pip install -e $(AIRLIFT_MODULE_DIR)
	uv pip install -e .

setup_local_env:
	$(MAKE) wipe
	mkdir -p $(AIRFLOW_HOME)
	mkdir -p $(DAGSTER_HOME)
	chmod +x $(AIRLIFT_MODULE_DIR)/scripts/airflow_setup.sh
	$(AIRLIFT_MODULE_DIR)/scripts/airflow_setup.sh $(MAKEFILE_DIR)/kitchen_sink/airflow_dags $(AIRFLOW_HOME)

run_airflow:
	airflow standalone

run_dagster_mapped:
	dagster dev -m kitchen_sink.dagster_defs.mapped_defs -p 3333

run_dagster_automapped:
	dagster dev -m kitchen_sink.dagster_defs.automapped_defs -p 3333

run_observation_defs:
	dagster dev -m kitchen_sink.dagster_defs.observation_defs -p 3333

# Command to point at a workspace.yaml
run_dagster_multi_code_locations:
	dagster dev -w $(MAKEFILE_DIR)/kitchen_sink/dagster_multi_code_locations/workspace.yaml -p 3333

wipe: ## Wipe out all the files created by the Makefile
	rm -rf $(AIRFLOW_HOME) $(DAGSTER_HOME)

wipe_dagster: ## Wipe out all the files created by the Makefile
	rm -rf $$DAGSTER_HOME