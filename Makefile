pylint:
	pylint -j 0 `git ls-files '*.py'` --rcfile=.pylintrc

update_doc_snapshot:
	pytest docs --snapshot-update

black:
	black examples python_modules --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

check_black:
	black examples python_modules --check --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

install_dev_python_modules:
	# NOTE: previously, we did a pip install --upgrade pip here. We have removed that and instead
	# depend on the user to ensure an up-to-date pip is installed and available. For context, there
	# is a lengthy discussion here:
	# https://github.com/pypa/pip/issues/5599

	# On machines with less memory, pyspark install will fail... see:
	# https://stackoverflow.com/a/31526029/11295366
	pip --no-cache-dir install pyspark==2.4.0

	#
	# Dask installation will fail for Python 2.7 (Dask doesn't work w/ py27 on macOS)
	# See https://github.com/dagster-io/dagster/issues/1486

	# dagster-pandas must come before dasgtermill because of dependency
	# See https://github.com/dagster-io/dagster/issues/1485

	echo "\n\nInstalling dagster\n\n"
	pip install -e python_modules/dagster

	echo "\n\nInstalling dagster-graphql\n\n"
	pip install -e python_modules/dagster-graphql

	echo "\n\nInstalling dagit\n\n"
	pip install -e python_modules/dagit

	echo "\n\nInstalling dagster-pandas\n\n"
	pip install -e python_modules/libraries/dagster-pandas

	echo "\n\nInstalling dagstermill\n\n"
	pip install -e python_modules/dagstermill

	echo "\n\nInstalling dagster-airflow\n\n"
	SLUGIFY_USES_TEXT_UNIDECODE=yes pip install -e python_modules/dagster-airflow

	# This installation will fail for Python 2.7 (Dask doesn't work w/ py27 on macOS)
	-pip install -e python_modules/dagster-dask
	pip install -e python_modules/libraries/dagster-aws
	pip install -e python_modules/libraries/dagster-bash
	pip install -e python_modules/libraries/dagster-cron
	pip install -e python_modules/libraries/dagster-datadog
	pip install -e python_modules/libraries/dagster-dbt
	pip install -e python_modules/libraries/dagster-gcp
	pip install -e python_modules/libraries/dagster-ge
	pip install -e python_modules/libraries/dagster-pagerduty
	pip install -e python_modules/libraries/dagster-papertrail
	pip install -e python_modules/libraries/dagster-postgres
	pip install -e python_modules/libraries/dagster-pyspark
	pip install -e python_modules/libraries/dagster-slack
	pip install -e python_modules/libraries/dagster-snowflake
	pip install -e python_modules/libraries/dagster-spark
	pip install -e python_modules/libraries/dagster-ssh
	pip install -e python_modules/automation
	pip install -e examples[full]
	pip install -r python_modules/dagster/dev-requirements.txt
	pip install -r python_modules/dagit/dev-requirements.txt
	pip install -r python_modules/libraries/dagster-aws/dev-requirements.txt
	pip install -r bin/requirements.txt
	pip install -r .read-the-docs-requirements.txt
	pip install -r scala_modules/scripts/requirements.txt

graphql:
	cd js_modules/dagit/; make generate-types

rebuild_dagit:
	cd js_modules/dagit/; yarn install --offline && yarn build-for-python

dev_install: install_dev_python_modules rebuild_dagit

graphql_tests:
	pytest examples/dagster_examples_tests/graphql_tests/ python_modules/dagster-graphql/dagster_graphql_tests/graphql/ -s -vv
