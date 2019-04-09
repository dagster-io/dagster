# This is a hack because we are getting timeouts on CircleCI running pylint on all the targets
# at once
pylint: 
	set -e;
	for target in `cat .pylint_targets` ; do \
		echo $$target; \
		pylint -j 0 $$target --rcfile=.pylintrc --disable=R,C; \
	done;
	set +e;

black:
	black python_modules --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|python_modules/dagster/dagster/tutorials/|snapshots/|__scaffold\.py" -N
	black python_modules/dagster/dagster/tutorials examples --line-length 79 -S --fast -N

