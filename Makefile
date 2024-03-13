.PHONY: pyright

# Makefile oddities:
# - Commands must start with literal tab characters (\t), not spaces.
# - Multi-command rules (like `ruff` below) by default terminate as soon as a command has a non-0
#   exit status. Prefix the command with "-" to instruct make to continue to the next command
#   regardless of the preceding command's exit status.

pyright:
	python scripts/run-pyright.py --all

install_pyright:
	pip install -e 'python_modules/dagster[pyright]'

rebuild_pyright:
	python scripts/run-pyright.py --all --rebuild

# Skip typecheck so that this can be used to test if all requirements can successfully be resolved
# in CI independently of typechecking.
rebuild_pyright_pins:
	python scripts/run-pyright.py --update-pins --skip-typecheck

quick_pyright:
	python scripts/run-pyright.py --diff

unannotated_pyright:
	python scripts/run-pyright.py --unannotated

ruff:
	-ruff check --fix .
	ruff format .

check_ruff:
	ruff .
	ruff format --check .

check_prettier:
#NOTE:  excludes README.md because it's a symlink
	yarn exec --cwd js_modules/dagster-ui/packages/eslint-config -- prettier `git ls-files \
	'python_modules/*.yml' 'python_modules/*.yaml' 'helm/*.yml' 'helm/*.yaml' \
	':!:helm/**/templates/*.yml' ':!:helm/**/templates/*.yaml' '*.md' ':!:docs/*.md' \
	':!:README.md'` --check

prettier:
	yarn exec --cwd js_modules/dagster-ui/packages/eslint-config -- prettier `git ls-files \
	'python_modules/*.yml' 'python_modules/*.yaml' 'helm/*.yml' 'helm/*.yaml' \
	':!:helm/**/templates/*.yml' ':!:helm/**/templates/*.yaml' '*.md' ':!:docs/*.md' \
	':!:README.md'` --write

install_dev_python_modules:
	python scripts/install_dev_python_modules.py -qqq

install_dev_python_modules_verbose:
	python scripts/install_dev_python_modules.py

install_dev_python_modules_verbose_m1:
	python scripts/install_dev_python_modules.py -qqq --include-prebuilt-grpcio-wheel

graphql:
	cd js_modules/dagster-ui/; make generate-graphql; make generate-perms

sanity_check:
#NOTE:  fails on nonPOSIX-compliant shells (e.g. CMD, powershell)
#NOTE:  dagster-hex is an external package
	@echo Checking for prod installs - if any are listed below reinstall with 'pip -e'
	@! (pip list --exclude-editable | grep -e dagster | grep -v dagster-hex | grep -v dagster-hightouch)

rebuild_ui: sanity_check
	cd js_modules/dagster-ui/; yarn install && yarn build

rebuild_ui_with_profiling: sanity_check
	cd js_modules/dagster-ui/; yarn install && yarn build-with-profiling

dev_install_m1_grpcio_wheel: install_dev_python_modules_verbose_m1 rebuild_ui

dev_install: install_dev_python_modules_verbose rebuild_ui

dev_install_quiet: install_dev_python_modules rebuild_ui

graphql_tests:
	pytest python_modules/dagster-graphql/dagster_graphql_tests/graphql/ -s -vv

check_manifest:
	check-manifest python_modules/dagster
	check-manifest python_modules/dagster-webserver
	check-manifest python_modules/dagster-graphql
	ls python_modules/libraries | xargs -n 1 -Ipkg check-manifest python_modules/libraries/pkg
