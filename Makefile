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
	pip --no-cache-dir install pyspark\>=3.0.1 $(QUIET)

# Need to do this for 3.9 compat
# This is to ensure we can build Pandas on 3.9
# See: https://github.com/numpy/numpy/issues/17784,
	-python scripts/is_39.py && pip install Cython==0.29.21 numpy==1.18.5

# NOTE: These need to be installed as one long pip install command, otherwise pip will install
# conflicting dependencies, which will break pip freeze snapshot creation during the integration
# image build!
	pip install \
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
	    -e "python_modules/libraries/dagster-dask[yarn,pbs,kube]" \
	    -e python_modules/libraries/dagster-datadog \
	    -e python_modules/libraries/dagster-dbt \
	    -e python_modules/libraries/dagster-docker \
	    -e python_modules/libraries/dagster-gcp \
	    -e python_modules/libraries/dagster-ge \
	    -e python_modules/libraries/dagster-k8s \
	    -e python_modules/libraries/dagster-celery-k8s \
	    -e python_modules/libraries/dagster-pagerduty \
	    -e python_modules/libraries/dagster-papertrail \
	    -e python_modules/libraries/dagster-postgres \
	    -e python_modules/libraries/dagster-prometheus \
	    -e python_modules/libraries/dagster-spark \
	    -e python_modules/libraries/dagster-pyspark \
	    -e python_modules/libraries/dagster-databricks \
	    -e python_modules/libraries/dagster-shell \
	    -e python_modules/libraries/dagster-slack \
	    -e python_modules/libraries/dagster-ssh \
	    -e python_modules/libraries/dagster-twilio \
	    -e python_modules/libraries/lakehouse \
	    -r python_modules/dagster/dev-requirements.txt \
	    -r python_modules/libraries/dagster-aws/dev-requirements.txt \
	    -e integration_tests/python_modules/dagster-k8s-test-infra \
	    -r scala_modules/scripts/requirements.txt \
	    $(QUIET)

# Can't install dagster-airflow right now:
# https://github.com/dagster-io/dagster/issues/3488

# Don't install dagster-azure as part of this target _yet_ - it has a dependency
# conflict with dagster-snowflake which causes any import of dagster-snowflake to
# fail with an ImportError (e.g. in examples).
# Uncomment only when snowflake-connector-python can be installed with optional (or compatible)
# Azure dependencies.
# See https://github.com/dagster-io/dagster/pull/2483#issuecomment-635174157
# pip install -e python_modules/libraries/dagster-azure $(QUIET)

# incompatible with python 3.9 below
# minus prefix ignores non-zero exit code
	-python scripts/is_39.py || \
	pip install \
	    -e python_modules/libraries/dagster-snowflake \
	    -e python_modules/libraries/dagstermill \
	    -e examples/legacy_examples[full] \
	    -e examples/airline_demo[full] \
	    -r docs-requirements.txt $(QUIET)


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
