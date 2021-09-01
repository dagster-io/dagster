pylint:
	pylint -j 0 `git ls-files '*.py'` --rcfile=.pylintrc

update_doc_snapshot:
	pytest docs --snapshot-update

black:
	black examples integration_tests helm python_modules .buildkite --line-length 100 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/|intro_tutorial/"
	black examples/docs_snippets/docs_snippets/intro_tutorial --line-length 78 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/"
	black examples/docs_snippets_crag/docs_snippets_crag/intro_tutorial --line-length 78 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/"

check_black:
	black examples integration_tests helm python_modules .buildkite --check --line-length 100 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/|intro_tutorial/"
	black examples/docs_snippets/docs_snippets/intro_tutorial --check --line-length 78 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/"
	black examples/docs_snippets_crag/docs_snippets_crag/intro_tutorial --check --line-length 78 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/"

isort:
	isort `git ls-files '*.py' ':!:examples/docs_snippets/docs_snippets/intro_tutorial' ':!:examples/docs_snippets_crag/docs_snippets_crag/intro_tutorial/*.py'`
	isort -l 78 `git ls-files 'examples/docs_snippets/docs_snippets/intro_tutorial/*.py'`
	isort -l 78 `git ls-files 'examples/docs_snippets_crag/docs_snippets_crag/intro_tutorial/*.py'`

yamllint:
	yamllint -c .yamllint.yaml --strict `git ls-files 'helm/**/*.yml' 'helm/**/*.yaml' ':!:helm/**/templates/*.yml' ':!:helm/**/templates/*.yaml'`

install_dev_python_modules:
	python scripts/install_dev_python_modules.py -qqq

install_dev_python_modules_verbose:
	python scripts/install_dev_python_modules.py

graphql:
	cd js_modules/dagit/; make generate-graphql

sanity_check:
#NOTE:  fails on nonPOSIX-compliant shells (e.g. CMD, powershell)
	@echo Checking for prod installs - if any are listed below reinstall with 'pip -e'
	@! (pip list --exclude-editable | grep -e dagster -e dagit)

rebuild_dagit: sanity_check
	cd js_modules/dagit/; yarn install && yarn build-for-python

dev_install: install_dev_python_modules_verbose rebuild_dagit

dev_install_quiet: install_dev_python_modules rebuild_dagit

graphql_tests:
	pytest python_modules/dagster-graphql/dagster_graphql_tests/graphql/ -s -vv

check_manifest:
	check-manifest python_modules/dagster
	check-manifest python_modules/dagit
	check-manifest python_modules/dagster-graphql
	ls python_modules/libraries | xargs -n 1 -Ipkg check-manifest python_modules/libraries/pkg
