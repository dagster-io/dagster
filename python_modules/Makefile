watch:
	watchmedo shell-command --recursive --patterns="*.py" -i "*.pyc"  --command \
	"pytest -vvx --ff "\
	"dagster/dagster_tests "\
	"dagit/dagit_tests "\
	"dagster-pandas/dagster_pandas_tests "\
	"dagster-ge/dagster_ge_tests " \
	--drop dagster/dagster dagster/dagster_tests/ dagster-ge/dagster_ge dagster-ge/dagster_ge_tests dagit/dagit dagit/dagit_tests

black:
	black . --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|python_modules/dagster/dagster/tutorials/|snapshots/|__scaffold\.py" -N
	black ./dagster/dagster/tutorials --line-length 79 -S --fast -N


pylint:
	pylint -j 0 --disable=R,C dagster/dagster dagster/dagster_tests dagit/dagit dagit/dagit_tests dagstermill/dagstermill dagster-pandas/dagster_pandas dagster-sqlalchemy/dagster_sqlalchemy dagster-graphql/dagster_graphql --rcfile=../.pylintrc

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

intro_tutorial:
	cd dagster/dagster/tutorials/intro_tutorial; dagit -p 3333

docs:
	pytest --snapshot-update dagster

clean:
	find . -name \*.pyc -delete
	rm -rf ./dagster/docs/_build
	rm -rf ./dagster/htmlcov/
	rm -rf ./dagster/build/
