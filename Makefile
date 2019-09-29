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
	pip --no-cache-dir install pyspark==2.4.0 -qqq

# dagster-pandas must come before dasgtermill because of dependency
# See https://github.com/dagster-io/dagster/issues/1485

	@echo "\n\nInstalling dagster"
	pip install -e python_modules/dagster -qqq

	@echo "\n\nInstalling dagster-graphql"
	pip install -e python_modules/dagster-graphql -qqq

	@echo "\n\nInstalling dagit"
	pip install -e python_modules/dagit -qqq

	@echo "\n\nInstalling dagster-pandas"
	pip install -e python_modules/libraries/dagster-pandas -qqq

	@echo "\n\nInstalling dagstermill"
	pip install -e python_modules/dagstermill -qqq

	@echo "\n\nInstalling dagster-airflow"
	SLUGIFY_USES_TEXT_UNIDECODE=yes pip install -e python_modules/dagster-airflow -qqq

	# NOTE: This installation will fail for Python 2.7 (Dask doesn't work w/ py27 on macOS)
	-pip install -e python_modules/dagster-dask -qqq
	pip install -e python_modules/libraries/dagster-aws -qqq
	pip install -e python_modules/libraries/dagster-bash -qqq
	pip install -e python_modules/libraries/dagster-cron -qqq
	pip install -e python_modules/libraries/dagster-datadog -qqq
	pip install -e python_modules/libraries/dagster-dbt -qqq
	pip install -e python_modules/libraries/dagster-gcp -qqq
	pip install -e python_modules/libraries/dagster-ge -qqq
	pip install -e python_modules/libraries/dagster-pagerduty -qqq
	pip install -e python_modules/libraries/dagster-papertrail -qqq
	pip install -e python_modules/libraries/dagster-postgres -qqq
	pip install -e python_modules/libraries/dagster-pyspark -qqq
	pip install -e python_modules/libraries/dagster-slack -qqq
	pip install -e python_modules/libraries/dagster-snowflake -qqq
	pip install -e python_modules/libraries/dagster-spark -qqq
	pip install -e python_modules/libraries/dagster-ssh -qqq
	pip install -e python_modules/libraries/dagster-twilio -qqq
	pip install -e python_modules/automation -qqq
	pip install -e examples[full] -qqq
	pip install -r python_modules/dagster/dev-requirements.txt -qqq
	pip install -r python_modules/dagit/dev-requirements.txt -qqq
	pip install -r python_modules/libraries/dagster-aws/dev-requirements.txt -qqq
	pip install -r bin/requirements.txt -qqq
	pip install -r .read-the-docs-requirements.txt -qqq
	pip install -r scala_modules/scripts/requirements.txt -qqq

graphql:
	cd js_modules/dagit/; make generate-types

rebuild_dagit:
	cd js_modules/dagit/; yarn install --offline && yarn build-for-python

dev_install: install_dev_python_modules rebuild_dagit

graphql_tests:
	pytest examples/dagster_examples_tests/graphql_tests/ python_modules/dagster-graphql/dagster_graphql_tests/graphql/ -s -vv
