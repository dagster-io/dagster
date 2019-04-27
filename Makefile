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
	pytest python_modules/dagster/docs --snapshot-update

black:
	black python_modules --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

check_black:
	black python_modules --check --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

dev_install:
	pip install -r python_modules/dagster/dev-requirements.txt -qqq
	pip install -e python_modules/dagster -qqq
	pip install -e python_modules/dagster-graphql -qqq
	pip install -e python_modules/dagit -qqq
	pip install -r python_modules/dagit/dev-requirements.txt -qqq
	pip install -e python_modules/dagstermill -qqq
	SLUGIFY_USES_TEXT_UNIDECODE=yes pip install -e python_modules/dagster-airflow -qqq
	pip install -e python_modules/libraries/dagster-aws -qqq
	pip install -e python_modules/libraries/dagster-gcp -qqq
	pip install -e python_modules/libraries/dagster-ge -qqq
	pip install -e python_modules/libraries/dagster-pandas -qqq
	pip install -e python_modules/libraries/dagster-snowflake -qqq
	pip install -e python_modules/libraries/dagster-spark -qqq
	pip install -e python_modules/libraries/dagster-pyspark -qqq
	pip install -e python_modules/automation -qqq
	pip install -e examples/event-pipeline-demo -qqq
	pip install -e examples/airline-demo -qqq