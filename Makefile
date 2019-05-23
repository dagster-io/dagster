# This is a hack because we are getting timeouts on CircleCI running pylint on all the targets
# at once
pylint-iterative:
	set -e;
	for target in `cat .pylint_targets` ; do \
		echo $$target; \
		pylint -j 0 $$target --rcfile=.pylintrc --disable=R,C || exit 1;\
	done;
	set +e;

pylint:
	pylint -j 0 `cat .pylint_targets` --rcfile=.pylintrc --disable=R,C

update_doc_snapshot:
	pytest docs --snapshot-update

black:
	black examples python_modules --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

check_black:
	black examples python_modules --check --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

install_dev_python_modules:
	pip install --upgrade pip
	pip install -r python_modules/dagster/dev-requirements.txt
	pip install -e python_modules/dagster
	pip install -e python_modules/dagster-graphql
	pip install -e python_modules/dagit
	pip install -r python_modules/dagit/dev-requirements.txt
	pip install -e python_modules/dagstermill
	SLUGIFY_USES_TEXT_UNIDECODE=yes pip install -e python_modules/dagster-airflow
	pip install -e python_modules/libraries/dagster-aws
	pip install -r python_modules/libraries/dagster-aws/dev-requirements.txt
	pip install -e python_modules/libraries/dagster-gcp
	pip install -e python_modules/libraries/dagster-ge
	pip install -e python_modules/libraries/dagster-pandas
	pip install -e python_modules/libraries/dagster-snowflake
	pip install -e python_modules/libraries/dagster-spark
	pip install -e python_modules/libraries/dagster-pyspark
	pip install -e python_modules/automation
	pip install -e examples

graphql:
	cd js_modules/dagit/; make generate-types

rebuild_dagit:
	cd js_modules/dagit/; yarn install && yarn build-for-python

dev_install: install_dev_python_modules rebuild_dagit
