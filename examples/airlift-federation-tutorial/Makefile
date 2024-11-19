.PHONY: help

define GET_MAKEFILE_DIR
$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))) | sed 's:/*$$::')
endef

MAKEFILE_DIR := $(GET_MAKEFILE_DIR)
export TUTORIAL_EXAMPLE_DIR := $(MAKEFILE_DIR)
export DAGSTER_HOME := $(MAKEFILE_DIR)/.dagster_home
export WAREHOUSE_AIRFLOW_HOME := $(MAKEFILE_DIR)/.warehouse_airflow_home
export METRICS_AIRFLOW_HOME := $(MAKEFILE_DIR)/.metrics_airflow_home
export DAGSTER_URL := http://localhost:3000

# Detect OS and use appropriate date command
UNAME_S := $(shell uname -s)
ifeq ($(UNAME_S),Darwin)
    TOMORROW_DATE := $(shell date -v+1d +"%Y-%m-%d")
else
    TOMORROW_DATE := $(shell date -d "+1 day" +"%Y-%m-%d")
endif

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'


### TUTORIAL COMMANDS ###
airflow_install:
	pip install uv && \
	uv pip install dagster-airlift[tutorial] && \
	uv pip install -e $(MAKEFILE_DIR)

airflow_setup: wipe
	mkdir -p $$WAREHOUSE_AIRFLOW_HOME
	mkdir -p $$METRICS_AIRFLOW_HOME
	mkdir -p $$DAGSTER_HOME
	chmod +x $(MAKEFILE_DIR)/scripts/airflow_setup.sh
	$(MAKEFILE_DIR)/scripts/airflow_setup.sh $(MAKEFILE_DIR)/airlift_federation_tutorial/warehouse_airflow_dags $(WAREHOUSE_AIRFLOW_HOME) 8081
	$(MAKEFILE_DIR)/scripts/airflow_setup.sh $(MAKEFILE_DIR)/airlift_federation_tutorial/metrics_airflow_dags $(METRICS_AIRFLOW_HOME) 8082

warehouse_airflow_run:
	AIRFLOW_HOME=$(WAREHOUSE_AIRFLOW_HOME) airflow standalone

metrics_airflow_run:
	AIRFLOW_HOME=$(METRICS_AIRFLOW_HOME) airflow standalone

dagster_run:
	dagster dev -m airlift_federation_tutorial.dagster_defs.definitions -p 3000

clean:
	airflow db clean --yes --clean-before-timestamp $(TOMORROW_DATE)
	dagster asset wipe --all --noprompt

update_readme_snippets:
	python ../../scripts/update_readme_snippets.py $(MAKEFILE_DIR)/README.md

wipe:
	rm -rf $$WAREHOUSE_AIRFLOW_HOME $$METRICS_AIRFLOW_HOME $$DAGSTER_HOME

