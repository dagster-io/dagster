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
	black ./dagster/dagster/tutorials ../examples --line-length 79 -S --fast -N


pylint:
<<<<<<< HEAD
	cd ../; pylint -j 0 --disable=R,C `cat .pylint_targets` --rcfile=.pylintrc
=======
	pylint -j 0 --disable=R,C \
	dagster/dagster dagster/dagster_tests \
	dagster-graphql/dagster_graphql dagster-graphql/dagster_graphql_tests \
	dagit/dagit dagit/dagit_tests \
	dagstermill/dagstermill dagstermill/dagstermill_tests \
	dagster-airflow/dagster_airflow dagster-airflow/dagster_airflow_tests \
	libraries/dagster-aws/dagster_aws libraries/dagster-aws/dagster_aws_tests \
	libraries/dagster-ge/dagster_ge libraries/dagster-ge/dagster_ge_tests \
	libraries/dagster-pandas/dagster_pandas libraries/dagster-pandas/dagster_pandas_tests \
	libraries/dagster-snowflake/dagster_snowflake libraries/dagster-snowflake/dagster_snowflake_tests \
	libraries/dagster-spark/dagster_spark libraries/dagster-spark/dagster_spark_tests \
	libraries/dagster-sqlalchemy/dagster_sqlalchemy libraries/dagster-sqlalchemy/dagster_sqlalchemy_tests \
	airline-demo/airline_demo airline-demo/airline_demo_tests \
	event-pipeline-demo/event_pipeline_demo event-pipeline-demo/event_pipeline_demo_tests \
	automation/
	--rcfile=../.pylintrc
>>>>>>> Fixup make pylint

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
