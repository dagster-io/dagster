.PHONY: help

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

ruff_snippets:  ## Ruff linting and fixing on /examples/docs_snippets
	-ruff check --fix ../examples/docs_snippets
	ruff format ../examples/docs_snippets

rebuild_kind_tags: ## Add all kind tags to the kind tags page
	python scripts/regen_kind_tags.py

mdx:
	tox -e sphinx-mdx

mdx_copy:
	cp -rf sphinx/_build/mdx/sections/api/apidocs/* docs-beta/docs/api/python-api/

regenerate_cli_snippets:
	cd ../examples/docs_beta_snippets && tox -e docs_snapshot_update && echo "\nSnippets regenerated!"

regenerate_cli_snippets_and_test:
	cd ../examples/docs_beta_snippets && tox -e docs_snapshot_update && tox -e docs_snapshot_test && echo "\nSnippets regenerated and tested!"

test_cli_snippets_simulate_bk:
	docker run --platform linux/amd64 --rm -it  -v "$(DAGSTER_GIT_REPO_DIR):/dagster" --entrypoint /bin/sh dagster/buildkite-test:py3.9-2025-01-31T181043 -c 'cd /dagster/examples/docs_beta_snippets && tox -e docs_snapshot_test -- --pdb'
