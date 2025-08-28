.PHONY: help

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

ruff_snippets:  ## Ruff linting and fixing on /examples/docs_snippets
	-ruff check --fix ../examples/docs_snippets
	ruff format ../examples/docs_snippets

rebuild_kind_tags: ## Add all kind tags to the kind tags page
	python scripts/regen_kind_tags.py

mdx:
	@echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
	@echo "DEPRECATED - use \`yarn build-api-docs\`"
	@echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
	tox -e sphinx-mdx

mdx_copy:
	@echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
	@echo "DEPRECATED - use \`yarn build-api-docs\`"
	@echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
	cp -rf sphinx/_build/mdx/sections/api/apidocs/* docs/api/python-api/

sphinx_objects_inv:
	@echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
	@echo "DEPRECATED - use \`yarn build-api-docs\`"
	@echo "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~"
	tox -e sphinx
	cp sphinx/_build/json/objects.inv static/.

regenerate_cli_snippets:
	cd ../examples/docs_snippets && tox -e docs_snapshot_update && echo "\nSnippets regenerated!"

regenerate_cli_snippets_and_screenshots:
	cd ../examples/docs_snippets && EXTRA_PARAMS='--update-screenshots' tox -e docs_snapshot_update && echo "\nSnippets regenerated!"

regenerate_cli_snippets_and_test:
	cd ../examples/docs_snippets && tox -e docs_snapshot_update && tox -e docs_snapshot_test && echo "\nSnippets regenerated and tested!"

regenerate_cli_snippets_and_test_debug:
	cd ../examples/docs_snippets && rm -rf /tmp/cli_snippets && mkdir -p /tmp/cli_snippets && (DAGSTER_CLI_SNIPPET_WORKING_DIR=/tmp/cli_snippets tox -e docs_snapshot_update && DAGSTER_CLI_SNIPPET_WORKING_DIR=/tmp/cli_snippets  tox -e docs_snapshot_test && echo "\nSnippets regenerated and tested!") || (echo "Snippet regeneration failed. Please check the logs for more information. Working directory: /tmp/cli_snippets" && exit 1)

test_cli_snippets_simulate_bk:
	docker run --platform linux/amd64 --rm -it  -v "$(DAGSTER_GIT_REPO_DIR):/dagster" --entrypoint /bin/sh dagster/buildkite-test:py3.9-2025-01-31T181043 -c 'cd /dagster/examples/docs_snippets && tox -e docs_snapshot_test -- --pdb'
