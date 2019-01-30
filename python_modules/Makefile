watch:
	watchmedo shell-command --recursive --patterns="*.py" -i "*.pyc"  --command \
	"pytest -vv "\
	"dagster/dagster/check/check_tests "\
	"dagster/dagster/cli/cli_tests "\
	"dagster/dagster/core/core_tests "\
	"dagster/dagster/dagster_examples/dagster_examples_tests "\
	"dagster/dagster/pandas/pandas_tests "\
	"dagster/dagster/sqlalchemy/sqlalchemy_tests "\
	"dagster/dagster/utils/utils_tests "\
	"dagster/dagster_tests "\
	"dagit/dagit_tests "\
	"dagster-ge/dagster_ge_tests " \
	--drop dagster/dagster dagster/dagster_tests/ dagster-ge/dagster_ge dagster-ge/dagster_ge_tests dagit/dagit dagit/dagit_tests

black:
	black . --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|python_modules/dagster/dagster/tutorials/|snapshots/|[a-zA-Z9-0_]*__scaffold.py"
	black ./dagster/dagster/tutorials --line-length 79 -S --fast


pylint:
	pylint -j 0 --disable=R,C dagster/dagster dagster/dagster_tests dagit/dagit dagit/dagit_tests dagstermill/dagstermill dagster-pandas/dagster_pandas dagster-sqlalchemy/dagster_sqlalchemy

reinstall:
	pip uninstall dagit
	pip uninstall dagster
	pip install -e dagster
	pip install -e dagit

rebuild_dagit:
	cd ../js_modules/dagit/; yarn install && yarn build-for-python

run_dagit:
	cd ../js_modules/dagit/; make

dagster_yapf:
	find dagster -name "*.py" | grep -v ".tox" | grep -v ".vscode" | grep -v "snapshots" | xargs yapf -i

test_airline:
	cd airline-demo; pytest -vv -s -W ignore:::psycopg2 -m "not slow and not py3"

clean:
	find . -name \*.pyc -delete
	rm -rf ./dagster/docs/_build
	rm -rf ./dagster/htmlcov/
	rm -rf ./dagster/build/
