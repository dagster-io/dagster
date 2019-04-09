pylint: 
	echo 'Linting:'
	echo `cat .pylint_targets`
	pylint -j 0 `cat .pylint_targets` --rcfile=.pylintrc --disable=R,C

black:
	black python_modules --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|python_modules/dagster/dagster/tutorials/|snapshots/|__scaffold\.py" -N
	black python_modules/dagster/dagster/tutorials examples --line-length 79 -S --fast -N

