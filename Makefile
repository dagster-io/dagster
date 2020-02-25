pylint:
	pylint -j 0 `git ls-files '*.py'` --rcfile=.pylintrc

update_doc_snapshot:
	pytest docs --snapshot-update

black:
	black examples python_modules --line-length 100 --target-version py27 --target-version py35 --target-version py36 --target-version py37 --target-version py38 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/|intro_tutorial/"
	black examples/dagster_examples/intro_tutorial --line-length 78 --target-version py35 --target-version py36 --target-version py37 --target-version py38 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/"

check_black:
	black examples python_modules --check --line-length 100 --target-version py27 --target-version py35 --target-version py36 --target-version py37 --target-version py38 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/|intro_tutorial/"
	black examples/dagster_examples/intro_tutorial --check --line-length 78 --target-version py27 --target-version py35 --target-version py36 --target-version py37 --target-version py38 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/"

isort:
	isort `git ls-files '*.py' ':!:examples/dagster_examples/intro_tutorial'`
	isort -l 78 `git ls-files 'examples/dagster_examples/intro_tutorial/*.py'`


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
# dagster-pandas must come before dasgtermill because of dependency
# See https://github.com/dagster-io/dagster/issues/1485

	pip install apache-airflow \
				-e python_modules/dagster \
				-e python_modules/dagster-graphql \
				-e python_modules/dagit \
				-e python_modules/libraries/dagster-pandas \
				-e python_modules/dagstermill \
				-e python_modules/libraries/dagster-aws \
				-e python_modules/libraries/dagster-bash \
				-e python_modules/libraries/dagster-celery \
				-e python_modules/libraries/dagster-cron \
				-e python_modules/libraries/dagster-datadog \
				-e python_modules/libraries/dagster-dbt \
				-e python_modules/libraries/dagster-gcp \
				-e python_modules/libraries/dagster-ge \
				-e python_modules/libraries/dagster-github \
				-e python_modules/libraries/dagster-k8s \
				-e python_modules/libraries/dagster-pagerduty \
				-e python_modules/libraries/dagster-papertrail \
				-e python_modules/libraries/dagster-postgres \
				-e python_modules/libraries/dagster-spark \
				-e python_modules/libraries/dagster-pyspark \
				-e python_modules/libraries/dagster-slack \
				-e python_modules/libraries/dagster-snowflake \
				-e python_modules/libraries/dagster-ssh \
				-e python_modules/libraries/dagster-twilio \
				-e python_modules/automation \
				-r python_modules/dagster/dev-requirements.txt \
				-r python_modules/libraries/dagster-aws/dev-requirements.txt \
				-r bin/requirements.txt \
				-r scala_modules/scripts/requirements.txt $(QUIET)

	SLUGIFY_USES_TEXT_UNIDECODE=yes pip install -e python_modules/libraries/dagster-airflow $(QUIET)

	# This fails on Python 3.8 because TensorFlow is missing
	-pip install -e examples[full] $(QUIET)

	# NOTE: This installation will fail for Python 2.7 (Dask doesn't work w/ py27 on macOS)
	-pip install -e python_modules/libraries/dagster-dask $(QUIET)

	pip install -r .read-the-docs-requirements.txt

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
