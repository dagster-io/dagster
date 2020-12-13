pylint:
	pylint -j 0 `git ls-files '*.py'` --rcfile=.pylintrc

update_doc_snapshot:
	pytest docs --snapshot-update

black:
	black examples integration_tests python_modules .buildkite --line-length 100 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/|intro_tutorial/"
	black examples/docs_snippets/docs_snippets/intro_tutorial --line-length 78 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/"

check_black:
	black examples python_modules .buildkite --check --line-length 100 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/|intro_tutorial/"
	black examples/docs_snippets/docs_snippets/intro_tutorial --check --line-length 78 --target-version py36 --target-version py37 --target-version py38 --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/"

isort:
	isort `git ls-files '*.py' ':!:examples/docs_snippets/docs_snippets/intro_tutorial'`
	isort -l 78 `git ls-files 'examples/docs_snippets/docs_snippets/intro_tutorial/*.py'`

yamllint:
	yamllint -c .yamllint.yaml --strict `git ls-files 'helm/dagster/*.yml' 'helm/dagster/*.yaml' ':!:helm/dagster/templates/*.yml' ':!:helm/dagster/templates/*.yaml'`

QUIET="-qqq"

install_dev_python_modules:
# NOTE: Especially on OSX, there are still many missing wheels for Python 3.9, which means that some
# dependencies may have to be built from source. You may find yourself needing to install system
# packages such as freetype, gfortran, etc.; on OSX, Homebrew should suffice.

# Tensorflow is still not available for 3.9 (2020-12-10), so we have put conditional logic in place
# around examples, etc., that make use of it. https://github.com/tensorflow/tensorflow/issues/44485

# Pyarrow is still not available for 3.9 (2020-12-10). https://github.com/apache/arrow/pull/8386

# As a consequence of pyarrow, the snowflake connector also is not yet avaialble for 3.9 (2020-12-10).
# https://github.com/snowflakedb/snowflake-connector-python/issues/562

# NOTE: previously, we did a pip install --upgrade pip here. We have removed that and instead
# depend on the user to ensure an up-to-date pip is installed and available. For context, there
# is a lengthy discussion here: https://github.com/pypa/pip/issues/5599

# On machines with less memory, pyspark install will fail... see:
# https://stackoverflow.com/a/31526029/11295366
	pip --no-cache-dir install pyspark\>=3.0.0 $(QUIET)

# This is to ensure we can build Pandas on 3.9
	-python scripts/is_39.py && pip install Cython==0.29.21

# Need to do this for 3.9 compat
# See: https://github.com/numpy/numpy/issues/17784,
	-python scripts/is_39.py && pip install numpy==1.18.5

# Need to manually install Airflow because we no longer explicitly depend on it
# dagster-pandas must come before dagstermill because of dependency
# See https://github.com/dagster-io/dagster/issues/1485

	pip install	apache-airflow==1.10.10
	pip install -e python_modules/dagster
	pip install -e python_modules/dagster-graphql
	pip install -e python_modules/dagster-test
	pip install -e python_modules/dagit
	pip install -e python_modules/automation
	pip install -e python_modules/libraries/dagster-pandas
	pip install -e python_modules/libraries/dagster-aws
	pip install -e python_modules/libraries/dagster-celery
	pip install -e python_modules/libraries/dagster-celery-docker
	pip install -e python_modules/libraries/dagster-cron
	pip install -e "python_modules/libraries/dagster-dask[yarn,pbs,kube]"
	pip install -e python_modules/libraries/dagster-datadog
	pip install -e python_modules/libraries/dagster-dbt
	pip install -e python_modules/libraries/dagster-docker
	pip install -e python_modules/libraries/dagster-gcp
	pip install -e python_modules/libraries/dagster-ge
	pip install -e python_modules/libraries/dagster-k8s
	pip install -e python_modules/libraries/dagster-celery-k8s
	pip install -e python_modules/libraries/dagster-pagerduty
	pip install -e python_modules/libraries/dagster-papertrail
	pip install -e python_modules/libraries/dagster-postgres
	pip install -e python_modules/libraries/dagster-prometheus
	pip install -e python_modules/libraries/dagster-spark
	pip install -e python_modules/libraries/dagster-pyspark
	pip install -e python_modules/libraries/dagster-databricks
	pip install -e python_modules/libraries/dagster-shell
	pip install -e python_modules/libraries/dagster-slack
	pip install -e python_modules/libraries/dagster-ssh
	pip install -e python_modules/libraries/dagster-twilio
	pip install -e python_modules/libraries/lakehouse
	pip install -r python_modules/dagster/dev-requirements.txt $(QUIET)
	pip install -r python_modules/libraries/dagster-aws/dev-requirements.txt
	pip install -e integration_tests/python_modules/dagster-k8s-test-infra
	pip install -r scala_modules/scripts/requirements.txt $(QUIET)

# Don't install dagster-azure as part of this target _yet_ - it has a dependency
# conflict with dagster-snowflake which causes any import of dagster-snowflake to
# fail with an ImportError (e.g. in examples).
# Uncomment only when snowflake-connector-python can be installed with optional (or compatible)
# Azure dependencies.
# See https://github.com/dagster-io/dagster/pull/2483#issuecomment-635174157
# pip install -e python_modules/libraries/dagster-azure $(QUIET)

	set SLUGIFY_USES_TEXT_UNIDECODE=yes

	pip install -e python_modules/libraries/dagster-airflow $(QUIET)

# incompatible with python 3.9 below
# minus prefix ignores non-zero exit code
	-python scripts/is_39.py || pip install -e python_modules/libraries/dagster-snowflake
	-python scripts/is_39.py || pip install -e python_modules/libraries/dagstermill 
	-python scripts/is_39.py || pip install	-e examples/legacy_examples[full]
	-python scripts/is_39.py || pip install -e examples/airline_demo[full]
	-python scripts/is_39.py || pip install -r docs-requirements.txt $(QUIET)

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
