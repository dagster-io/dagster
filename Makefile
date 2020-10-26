pylint:
	pylint -j 0 `git ls-files '*.py'` --rcfile=.pylintrc

update_doc_snapshot:
	pytest docs --snapshot-update

black:
	black examples integration_tests python_modules .buildkite --line-length 100 --target-version py27 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/|intro_tutorial/"
	black examples/docs_snippets/docs_snippets/intro_tutorial --line-length 78 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/"

check_black:
	black examples python_modules .buildkite --check --line-length 100 --target-version py27 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/|intro_tutorial/"
	black examples/docs_snippets/docs_snippets/intro_tutorial --check --line-length 78 --target-version py27 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/"

isort:
	isort `git ls-files '*.py' ':!:examples/docs_snippets/docs_snippets/intro_tutorial'`
	isort -l 78 `git ls-files 'examples/docs_snippets/docs_snippets/intro_tutorial/*.py'`

yamllint:
	yamllint -c .yamllint.yaml --strict `git ls-files 'helm/dagster/*.yml' 'helm/dagster/*.yaml' ':!:helm/dagster/templates/*.yml' ':!:helm/dagster/templates/*.yaml'`

QUIET="-qqq"

install_dev_python_modules:
# NOTE: previously, we did a pip install --upgrade pip here. We have removed that and instead
# depend on the user to ensure an up-to-date pip is installed and available. For context, there
# is a lengthy discussion here:
# https://github.com/pypa/pip/issues/5599

# On machines with less memory, pyspark install will fail... see:
# https://stackoverflow.com/a/31526029/11295366
	pip --no-cache-dir install pyspark\>=3.0.0 $(QUIET)

# Need to manually install Airflow because we no longer explicitly depend on it
# dagster-pandas must come before dasgtermill because of dependency
# See https://github.com/dagster-io/dagster/issues/1485
# NOTE: These installations will fail for Python 2.7 (Flyte and Dask don't work w/ py27)

	pip install apache-airflow \
				-e python_modules/dagster \
				-e python_modules/dagster-graphql \
				-e python_modules/dagster-test \
				-e python_modules/dagit \
				-e python_modules/automation \
				-e python_modules/libraries/dagster-pandas \
				-e python_modules/libraries/dagster-aws \
				-e python_modules/libraries/dagster-celery \
				-e python_modules/libraries/dagster-celery-docker \
				-e python_modules/libraries/dagster-cron \
				-e python_modules/libraries/dagster-datadog \
				-e python_modules/libraries/dagster-gcp \
				-e python_modules/libraries/dagster-github \
				-e python_modules/libraries/dagster-k8s \
				-e python_modules/libraries/dagster-celery-k8s \
				-e python_modules/libraries/dagster-pagerduty \
				-e python_modules/libraries/dagster-papertrail \
				-e python_modules/libraries/dagster-postgres \
				-e python_modules/libraries/dagster-prometheus \
				-e python_modules/libraries/dagster-spark \
				-e python_modules/libraries/dagster-pyspark \
				-e python_modules/libraries/dagster-aws-pyspark \
				-e python_modules/libraries/dagster-databricks \
				-e python_modules/libraries/dagster-shell \
				-e python_modules/libraries/dagster-slack \
				-e python_modules/libraries/dagster-snowflake \
				-e python_modules/libraries/dagster-ssh \
				-e python_modules/libraries/dagster-twilio \
				-e python_modules/libraries/dagstermill \
				-e python_modules/libraries/lakehouse \
				-r python_modules/libraries/dagster-aws/dev-requirements.txt \
				-e examples/legacy_examples[full] \
				-e examples/airline_demo[full] \
				-e integration_tests/python_modules/dagster-k8s-test-infra \
				-r scala_modules/scripts/requirements.txt $(QUIET)

# Don't install dagster-azure as part of this target _yet_ - it has a dependency
# conflict with dagster-snowflake which causes any import of dagster-snowflake to
# fail with an ImportError (e.g. in examples).
# Uncomment only when snowflake-connector-python can be installed with optional (or compatible)
# Azure dependencies.
# See https://github.com/dagster-io/dagster/pull/2483#issuecomment-635174157
# pip install -e python_modules/libraries/dagster-azure $(QUIET)

	set SLUGIFY_USES_TEXT_UNIDECODE=yes

	pip install -e python_modules/libraries/dagster-airflow $(QUIET)

# python 3 only below
# minus prefix ignores non-zero exit code
	-pip install -e python_modules/libraries/dagster-ge $(QUIET)
	-pip install -e "python_modules/libraries/dagster-dask[yarn,pbs,kube]" $(QUIET)
	-pip install -r docs-requirements.txt $(QUIET)
	-pip install -r python_modules/dagster/dev-requirements.txt $(QUIET)
	-pip install -e python_modules/libraries/dagster-dbt $(QUIET)

install_dev_python_modules_verbose:
	make QUIET="" install_dev_python_modules

graphql:
	cd js_modules/dagit/; make generate-types

sanity_check:
#NOTE:  fails on nonPOSIX-compliant shells (e.g. CMD, powershell)
	echo Checking for prod installs - if any are listed below reinstall with 'pip -e'
	! (pip list --exclude-editable | grep -e dagster -e dagit)

rebuild_dagit: sanity_check
	cd js_modules/dagit/; yarn install && yarn build-for-python

dev_install: install_dev_python_modules_verbose rebuild_dagit

dev_install_quiet: install_dev_python_modules rebuild_dagit

graphql_tests:
	pytest python_modules/dagster-graphql/dagster_graphql_tests/graphql/ -s -vv
