pylint:
	pylint -j 0 `git ls-files '*.py'` --rcfile=.pylintrc

update_doc_snapshot:
	pytest docs --snapshot-update

black:
	black examples python_modules --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/|intro_tutorial/" -N
	black examples/dagster_examples/intro_tutorial --line-length 78 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

check_black:
	black examples python_modules --check --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/|intro_tutorial/" -N
	black examples/dagster_examples/intro_tutorial --check --line-length 78 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

QUIET="-qqq"

install_dev_python_modules:
# NOTE: previously, we did a pip install --upgrade pip here. We have removed that and instead
# depend on the user to ensure an up-to-date pip is installed and available. For context, there
# is a lengthy discussion here:
# https://github.com/pypa/pip/issues/5599

# On machines with less memory, pyspark install will fail... see:
# https://stackoverflow.com/a/31526029/11295366
	pip --no-cache-dir install pyspark==2.4.4 $(QUIET)

# Need to manually install Airflow because we no longer explicitly depend on it
	pip install apache-airflow $(QUIET)

# dagster-pandas must come before dasgtermill because of dependency
# See https://github.com/dagster-io/dagster/issues/1485

	@echo "\n\nInstalling dagster"
	pip install -e python_modules/dagster $(QUIET)

	@echo "\n\nInstalling dagster-graphql"
	pip install -e python_modules/dagster-graphql $(QUIET)

	@echo "\n\nInstalling dagit"
	pip install -e python_modules/dagit $(QUIET)

	@echo "\n\nInstalling dagster-pandas"
	pip install -e python_modules/libraries/dagster-pandas $(QUIET)

	@echo "\n\nInstalling dagstermill"
	pip install -e python_modules/dagstermill $(QUIET)

	@echo "\n\nInstalling dagster-airflow"
	SLUGIFY_USES_TEXT_UNIDECODE=yes pip install -e python_modules/dagster-airflow $(QUIET)

	# NOTE: This installation will fail for Python 2.7 (Dask doesn't work w/ py27 on macOS)
	-pip install -e python_modules/dagster-dask $(QUIET)
	pip install -e python_modules/libraries/dagster-aws $(QUIET)
	pip install -e python_modules/libraries/dagster-bash $(QUIET)
	pip install -e python_modules/libraries/dagster-cron $(QUIET)
	pip install -e python_modules/libraries/dagster-datadog $(QUIET)
	pip install -e python_modules/libraries/dagster-dbt $(QUIET)
	pip install -e python_modules/libraries/dagster-gcp $(QUIET)
	pip install -e python_modules/libraries/dagster-ge $(QUIET)
	pip install -e python_modules/libraries/dagster-pagerduty $(QUIET)
	pip install -e python_modules/libraries/dagster-papertrail $(QUIET)
	pip install -e python_modules/libraries/dagster-postgres $(QUIET)
	pip install -e python_modules/libraries/dagster-pyspark $(QUIET)
	pip install -e python_modules/libraries/dagster-slack $(QUIET)
	pip install -e python_modules/libraries/dagster-snowflake $(QUIET)
	pip install -e python_modules/libraries/dagster-spark $(QUIET)
	pip install -e python_modules/libraries/dagster-ssh $(QUIET)
	pip install -e python_modules/libraries/dagster-twilio $(QUIET)
	pip install -e python_modules/automation $(QUIET)
	pip install -e examples[full] $(QUIET)
	pip install -r python_modules/dagster/dev-requirements.txt $(QUIET)
	pip install -r python_modules/dagit/dev-requirements.txt $(QUIET)
	pip install -r python_modules/libraries/dagster-aws/dev-requirements.txt $(QUIET)
	pip install -r bin/requirements.txt $(QUIET)
	pip install -r .read-the-docs-requirements.txt $(QUIET)
	pip install -r scala_modules/scripts/requirements.txt $(QUIET)

install_dev_python_modules_verbose:
	make QUIET="" install_dev_python_modules

graphql:
	cd js_modules/dagit/; make generate-types

sanity_check:
	! pip list --exclude-editable | grep -e dagster -e dagit

rebuild_dagit: sanity_check
	cd js_modules/dagit/; yarn install --offline && yarn build-for-python

dev_install: install_dev_python_modules rebuild_dagit

graphql_tests:
	pytest examples/dagster_examples_tests/graphql_tests/ python_modules/dagster-graphql/dagster_graphql_tests/graphql/ -s -vv
