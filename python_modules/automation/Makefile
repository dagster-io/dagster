dataproc:
	python -m automation.parse_dataproc_configs

	# Clean up formatting
	ruff check --fix --config ../../pyproject.toml ../libraries/dagster-gcp/dagster_gcp/dataproc/*.py
	ruff format --config ../../pyproject.toml ../libraries/dagster-gcp/dagster_gcp/dataproc/*.py

	# Clean up imports
	autoflake --in-place --remove-all-unused-imports ../libraries/dagster-gcp/dagster_gcp/dataproc/*.py

spark_docs:
	python -m automation.parse_spark_configs

	# Clean up formatting
	ruff check --fix --config ../../pyproject.toml ../libraries/dagster-spark/dagster_spark/configs_spark.py
	ruff check --fix --config ../../pyproject.toml ../libraries/dagster-aws/dagster_aws/emr/configs_spark.py
	ruff format --config ../../pyproject.toml ../libraries/dagster-spark/dagster_spark/configs_spark.py
	ruff format --config ../../pyproject.toml ../libraries/dagster-aws/dagster_aws/emr/configs_spark.py

	# Clean up imports
	autoflake --in-place --remove-all-unused-imports ../libraries/dagster-spark/dagster_spark/configs_spark.py
	autoflake --in-place --remove-all-unused-imports ../libraries/dagster-aws/dagster_aws/emr/configs_spark.py
