.PHONY: help

help:
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

docs_ruff:  ## Ruff linting and fixing on /examples/docs_snippets
	-ruff check --fix ../examples/docs_snippets
	ruff format ../examples/docs_snippets

apidoc-build:  ## Build Sphinx docs
	tox -e sphinx && python scripts/pack_json.py

apidoc-watch-build:  ## Watch build Sphinx docs
	watchmedo shell-command \
		--patterns='*.rst;conf.py;_ext/*.py' \
		--command='make apidoc-build' \
		--recursive \
		sphinx

next-dev-install:  ## Install Next.js dependencies
	cd next; yarn install

next-watch-build:  ## Run Next.js docs website in development mode
	cd next; yarn dev

mdx-format:  ## Format mdx files
	cd next; yarn mdx-format

mdx-full-format: docs_ruff mdx-format

rebuild-kind-tags-page: ## Add all kind tags to the kind tags page
	python scripts/regen_kind_tags.py

mdx:
	tox -e sphinx-mdx

mdx_copy:
	cp -rf sphinx/_build/mdx/sections/api/apidocs/* docs-beta/docs/api/
