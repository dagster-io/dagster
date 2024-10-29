.PHONY: help dev_install run_airflow wipe run_peer rm_proxied_state scaffold_observe run_observe scaffold_migrate run_migrate setup_local_env run_perf_scenarios_test run_perf_10_10 run_perf_150_1 run_perf_150_5

define GET_MAKEFILE_DIR
$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))) | sed 's:/*$$::')
endef

MAKEFILE_DIR := $(GET_MAKEFILE_DIR)
export DAGSTER_HOME := $(MAKEFILE_DIR)/.dagster_home
export AIRFLOW_HOME := $(MAKEFILE_DIR)/.airflow_home
export DAGSTER_URL := http://localhost:3333

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev_install:
	pip install uv
	uv pip install -e ../../../dagster-airlift
	uv pip install -e .

run_airflow: 
	airflow standalone

wipe: ## Wipe out all the files created by the Makefile
	rm -rf $(AIRFLOW_HOME) $(DAGSTER_HOME)

wipe_dagster: ## Wipe out all the files created by the Makefile
	rm -rf $(DAGSTER_HOME)

run_peer:
	dagster dev -m perf_harness.dagster_defs.peer

rm_proxied_state:
	rm -rf $(MAKEFILE_DIR)/perf_harness/airflow_dags/proxied_state

scaffold_observe: rm_proxied_state
	python $(MAKEFILE_DIR)/scripts/generate_yaml_files.py False

run_observe: scaffold_observe
	dagster dev -m perf_harness.dagster_defs.observe

scaffold_migrate: rm_proxied_state
	python $(MAKEFILE_DIR)/scripts/generate_yaml_files.py True

run_migrate: scaffold_migrate
	dagster dev -m perf_harness.dagster_defs.migrate

# make airflow home and dagster home directories within current directory, set up env vars, and then
# set up airflow environment.
setup_local_env: scaffold_observe
	$(MAKE) wipe
	mkdir -p $$AIRFLOW_HOME
	mkdir -p $$DAGSTER_HOME
	chmod +x ../../scripts/airflow_setup.sh
	../../scripts/airflow_setup.sh $(MAKEFILE_DIR)/perf_harness/airflow_dags

run_perf_scenarios_test:
	perf-harness 1 1 1

# 10 dags, 10 tasks, 1 asset per task
run_perf_10_10_1:
	perf-harness 10 10 1

# 150 dags, 1 task, 1 asset per task
run_perf_150_1_1:
	perf-harness 150 1 1

# 150 dags, 5 tasks, 1 asset per task
run_perf_1_100_1:
	perf-harness 1 100 1

# 2 dags, 20 tasks, 100 assets per task
run_perf_2_20_100:
	perf-harness 2 20 100