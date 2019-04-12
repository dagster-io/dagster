# This is a hack because we are getting timeouts on CircleCI running pylint on all the targets
# at once
pylint: 
	set -e;
	for target in `cat .pylint_targets` ; do \
		echo $$target; \
		pylint -j 0 $$target --rcfile=.pylintrc --disable=R,C; \
	done;
	set +e;

update_doc_snapshot:
	pytest python_modules/dagster/docs --snapshot-update

black:
	black python_modules --line-length 100 -S --fast --exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N
