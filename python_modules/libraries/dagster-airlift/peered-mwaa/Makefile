.PHONY: help

define GET_MAKEFILE_DIR
$(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))) | sed 's:/*$$::')
endef

export MAKEFILE_DIR := $(GET_MAKEFILE_DIR)
export DAGSTER_HOME := $(MAKEFILE_DIR)/.dagster_home
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
	mkdir -p $(DAGSTER_HOME)

wipe: ## Wipe out all the files created by the Makefile
	rm -rf $(DAGSTER_HOME)

wipe_dagster: ## Wipe out all the files created by the Makefile
	rm -rf $$DAGSTER_HOME