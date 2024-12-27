.PHONY: help

define GET_MAKEFILE_DIR
$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))) | sed 's:/*$$::')
endef

MAKEFILE_DIR := $(GET_MAKEFILE_DIR)
export DAGSTER_HOME := $(MAKEFILE_DIR)/.dagster_home
export DAGSTER_URL := http://localhost:3333

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

dev_install:
	pip install uv && \
	uv pip install -e ../../../dagster-airlift[core,mwaa] && \
	uv pip install -e .

# make dagster home directory within current directory, set up env vars, and then 
# set up airflow environment.
setup_local_env:
	make wipe && \
	mkdir -p $$DAGSTER_HOME

run_dagster_dev:
	dagster dev -m mwaa_example.definitions -p 3333

wipe: ## Wipe out all the files created by the Makefile
	rm -rf $$DAGSTER_HOME

update_mwaa:
	python $(MAKEFILE_DIR)/scripts/setup_mwaa.py \
		--region us-west-2 \
		--profile dev-cloud-admin \
		--bucket mwaa-shared-artifacts \
		--env-name airlift-mwaa-example \
		--dags-folder $(MAKEFILE_DIR)/dags