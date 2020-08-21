dataproc:
	python -m automation.parse_dataproc_configs

	# Clean up formatting
	black ../libraries/dagster-gcp/dagster_gcp/dataproc/ \
		--line-length 100 --fast \
		--exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

	# Clean up imports
	autoflake --in-place --remove-all-unused-imports ../libraries/dagster-gcp/dagster_gcp/dataproc/*.py

spark_docs:
	python -m automation.parse_spark_configs --output-file \
		../libraries/dagster-spark/dagster_spark/configs_spark.py

	# Clean up formatting
	black ../libraries/dagster-spark/dagster_spark/configs_spark.py \
		--line-length 100 --fast \
		--exclude "build/|buck-out/|dist/|_build/|\.eggs/|\.git/|\.hg/|\.mypy_cache/|\.nox/|\.tox/|\.venv/|snapshots/" -N

	# Clean up imports
	autoflake --in-place --remove-all-unused-imports ../libraries/dagster-spark/dagster_spark/configs_spark.py
