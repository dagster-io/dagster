.PHONY: help

define GET_MAKEFILE_DIR
$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))) | sed 's:/*$$::')
endef

export MAKEFILE_DIR := $(GET_MAKEFILE_DIR)
export DAGSTER_HOME := $(MAKEFILE_DIR)/.dagster_home
export MIGRATING_AIRFLOW_HOME := $(MAKEFILE_DIR)/.migrating_airflow_home
export FEDERATED_AIRFLOW_HOME_1 := $(MAKEFILE_DIR)/.federated_airflow_home
export FEDERATED_AIRFLOW_HOME_2 := $(MAKEFILE_DIR)/.federated_airflow_home_2
export DBT_PROJECT_DIR := $(MAKEFILE_DIR)/dbt_example/shared/dbt
export DBT_PROFILES_DIR := $(MAKEFILE_DIR)/dbt_example/shared/dbt
export DAGSTER_URL := http://localhost:3333
export AIRLIFT_MODULE_DIR := $(MAKEFILE_DIR)/../../python_modules/libraries/dagster-airlift
export DBT_CLOUD_MODULE_DIR := $(MAKEFILE_DIR)/../../python_modules/libraries/dagster-dbt

export COMPONENTS_DIR := $(MAKEFILE_DIR)/dbt_example/components

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dbt_setup: ## Initialize dbt project
	dbt seed

dev_install:
	pip install uv && \
	uv pip install -e $(DBT_CLOUD_MODULE_DIR) && \
	uv pip install -e $(AIRLIFT_MODULE_DIR)[test]
	uv pip install -e .

setup_local_env: 
	$(MAKE) wipe
	mkdir -p $(MIGRATING_AIRFLOW_HOME)
	mkdir -p $(FEDERATED_AIRFLOW_HOME_1)
	mkdir -p $(FEDERATED_AIRFLOW_HOME_2)
	mkdir -p $(DAGSTER_HOME)
	chmod +x $(AIRLIFT_MODULE_DIR)/scripts/airflow_setup.sh
	$(AIRLIFT_MODULE_DIR)/scripts/airflow_setup.sh $(MAKEFILE_DIR)/dbt_example/migrating_airflow_dags $(MIGRATING_AIRFLOW_HOME)
	$(AIRLIFT_MODULE_DIR)/scripts/airflow_setup.sh $(MAKEFILE_DIR)/dbt_example/federated_airflow_dags_1 $(FEDERATED_AIRFLOW_HOME_1) 8081
	$(AIRLIFT_MODULE_DIR)/scripts/airflow_setup.sh $(MAKEFILE_DIR)/dbt_example/federated_airflow_dags_2 $(FEDERATED_AIRFLOW_HOME_2) 8082
	$(MAKE) dbt_setup

no_proxy_file:
	rm -f $(MAKEFILE_DIR)/dbt_example/migrating_airflow_dags/proxied_state/rebuild_iris_models.yaml
	AIRFLOW_HOME=$(MIGRATING_AIRFLOW_HOME) airflow dags reserialize

not_proxied:
	rm -f $(MAKEFILE_DIR)/dbt_example/migrating_airflow_dags/proxied_state/rebuild_iris_models.yaml
	cp $(MAKEFILE_DIR)/dbt_example/migrating_airflow_dags/proxied_state/observe_rebuild_iris_models.yaml $(MAKEFILE_DIR)/dbt_example/migrating_airflow_dags/proxied_state/rebuild_iris_models.yaml
	AIRFLOW_HOME=$(MIGRATING_AIRFLOW_HOME) airflow dags reserialize

proxied: 
	rm -f $(MAKEFILE_DIR)/dbt_example/migrating_airflow_dags/proxied_state/rebuild_iris_models.yaml
	cp $(MAKEFILE_DIR)/dbt_example/migrating_airflow_dags/proxied_state/migrated_rebuild_iris_models.yaml $(MAKEFILE_DIR)/dbt_example/migrating_airflow_dags/proxied_state/rebuild_iris_models.yaml
	AIRFLOW_HOME=$(MIGRATING_AIRFLOW_HOME) airflow dags reserialize

run_migrating_airflow:
	AIRFLOW_HOME=$(MIGRATING_AIRFLOW_HOME) airflow standalone

run_federated_airflow_1:
	AIRFLOW_HOME=$(FEDERATED_AIRFLOW_HOME_1) airflow standalone

run_federated_airflow_2:
	AIRFLOW_HOME=$(FEDERATED_AIRFLOW_HOME_2) airflow standalone

run_peer: no_proxy_file
	dagster dev -m dbt_example.dagster_defs.peer -p 3333

run_observe: not_proxied
	dagster dev -m dbt_example.dagster_defs.observe -p 3333

run_observe_with_check: not_proxied
	dagster dev -m dbt_example.dagster_defs.observe_with_check -p 3333

run_migrate: proxied
	dagster dev -m dbt_example.dagster_defs.migrate -p 3333

run_complete:
	dagster dev -m dbt_example.dagster_defs.complete -p 3333

run_federated_airflow_defs_1:
	dagster dev -m dbt_example.dagster_defs.federated_airflow_defs_1 -p 3333

run_federated_airflow_defs_2:
	dagster dev -m dbt_example.dagster_defs.federated_airflow_defs_2 -p 3333

run_dbt_cloud_defs:
	dagster dev -m dbt_example.dagster_defs.dbt_cloud_airflow -p 3333

run_peer_component: no_proxy_file
	rm -f $(COMPONENTS_DIR)/inner/lakehouse/defs.yaml
	rm -f $(COMPONENTS_DIR)/inner/dbt_project/defs.yaml
	cp $(COMPONENTS_DIR)/inner/peer-defs.yaml $(COMPONENTS_DIR)/inner/defs.yaml
	DAGSTER_HOME=$(DAGSTER_HOME) dagster dev -m dbt_example.components.defs -p 3333 --verbose
run_observe_component: not_proxied
	rm -f $(COMPONENTS_DIR)/inner/lakehouse/defs.yaml
	rm -f $(COMPONENTS_DIR)/inner/dbt_project/defs.yaml
	cp -f $(COMPONENTS_DIR)/inner/dbt_project/_defs.yaml $(COMPONENTS_DIR)/inner/dbt_project/defs.yaml
	cp -f $(COMPONENTS_DIR)/inner/observe-defs.yaml $(COMPONENTS_DIR)/inner/defs.yaml
	DAGSTER_HOME=$(DAGSTER_HOME) dagster dev -m dbt_example.components.defs -p 3333 --verbose
run_migrate_component: proxied
	rm -f $(COMPONENTS_DIR)/inner/lakehouse/defs.yaml
	rm -f $(COMPONENTS_DIR)/inner/dbt_project/defs.yaml
	cp -f $(COMPONENTS_DIR)/inner/lakehouse/_defs.yaml $(COMPONENTS_DIR)/inner/lakehouse/defs.yaml
	cp -f $(COMPONENTS_DIR)/inner/dbt_project/_defs.yaml $(COMPONENTS_DIR)/inner/dbt_project/defs.yaml
	cp -f $(COMPONENTS_DIR)/inner/migrate-defs.yaml $(COMPONENTS_DIR)/inner/defs.yaml
	DAGSTER_HOME=$(DAGSTER_HOME) dagster dev -m dbt_example.components.defs -p 3333 --verbose


wipe: ## Wipe out all the files created by the Makefile
	rm -rf $(MIGRATING_AIRFLOW_HOME) $(FEDERATED_AIRFLOW_HOME_1) $(FEDERATED_AIRFLOW_HOME_2) $(DAGSTER_HOME)

wipe_dagster: ## Wipe out all the files created by the Makefile
	rm -rf $$DAGSTER_HOME
