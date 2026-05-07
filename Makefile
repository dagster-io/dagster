.PHONY: ty pyright

export COREPACK_ENABLE_DOWNLOAD_PROMPT := 0

# Makefile oddities:
# - Commands must start with literal tab characters (\t), not spaces.
# - Multi-command rules (like `ruff` below) by default terminate as soon as a command has a non-0
#   exit status. Prefix the command with "-" to instruct make to continue to the next command
#   regardless of the preceding command's exit status.

# Targets with a justfile equivalent delegate to just. CI uses just directly
# (the buildkite-test image no longer ships make). These wrappers exist for
# local developer convenience.

pyright:
	just pyright

install_prettier:
	just install_prettier

install_pyright:
	just install_pyright

rebuild_pyright:
	ulimit -Sn 4096 # pyright build uses a lot of open files
	python scripts/run-pyright.py --all --rebuild

rebuild_pyright_pins:
	just rebuild_pyright_pins

quick_pyright:
	python scripts/run-pyright.py --diff

unannotated_pyright:
	python scripts/run-pyright.py --unannotated

ty:
	just ty

rebuild_ty:
	python scripts/run-ty.py --all --rebuild

rebuild_ty_pins:
	just rebuild_ty_pins

quick_ty:
	python scripts/run-ty.py --diff

ruff:
	ruff check --fix .
	ruff format .

check_ruff:
	just check_ruff

unsafe_ruff:
	ruff check --fix --unsafe-fixes .
	ruff format .

check_prettier:
	just check_prettier

prettier:
	prettier `git ls-files \
	'python_modules/*.yml' 'python_modules/*.yaml' 'helm/*.yml' 'helm/*.yaml' \
	'*.md' '.claude/*.md' \
	':!:docs/*.md' ':!:helm/**/templates/*.yml' ':!:helm/**/templates/*.yaml' \
	':!:README.md' ':!:GEMINI.md'` \
	--write

install_dev_python_modules:
	python scripts/install_dev_python_modules.py -q

install_dev_python_modules_verbose:
	python scripts/install_dev_python_modules.py

install_dev_python_modules_verbose_m1:
	python scripts/install_dev_python_modules.py --include-prebuilt-grpcio-wheel

graphql_codegen_js:
	cd js_modules; make generate-graphql; make generate-perms

graphql_codegen_py:
	cd python_modules/libraries/dagster-rest-resources; uv run --active --no-project ariadne-codegen

graphql_codegen:
	make graphql_codegen_js;
	make graphql_codegen_py;

sanity_check:
#NOTE:  fails on nonPOSIX-compliant shells (e.g. CMD, powershell)
#NOTE:  dagster-hex is an external package
	@echo Checking for prod installs - if any are listed below reinstall with 'uv pip install -e'
	@! (uv pip list --exclude-editable | grep -e dagster | grep -v dagster-hex | grep -v dagster-hightouch)

rebuild_ui: sanity_check
	just rebuild_ui

rebuild_ui_with_profiling: sanity_check
	cd js_modules; yarn install && yarn build-with-profiling

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

format_docs:
	cd docs; yarn format
