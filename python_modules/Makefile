watch:
	watchmedo shell-command --recursive --patterns="*.py" -i "*.pyc"  --command \
	"pytest -vvx --ff "\
	"dagster/dagster_tests "\
	"dagster-graphql/dagster_graphql_tests "\
	"dagit/dagit_tests "

black:
	black . --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

reinstall:
	pip uninstall dagit
	pip uninstall dagster
	pip install -e dagster
	pip install -e dagit

rebuild_dagit:
	cd ../js_modules/dagit/; yarn install --offline && yarn build-for-python

run_dagit:
	cd ../js_modules/dagit/; make

test_airline:
	cd airline-demo; pytest -vv -s -W ignore:::psycopg2 -m "not slow and not py3"

intro_tutorial:
	cd dagster/dagster/tutorials/intro_tutorial; dagit -p 3333

docs:
	pytest --snapshot-update dagster

clean:
	find . -name \*.pyc -delete
	rm -rf ./dagster/htmlcov/
	rm -rf ./dagster/build/
