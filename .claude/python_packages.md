# python package locations

Quick reference for Python packages in the Dagster repository.

## core packages

**dagster**: `python_modules/dagster`
**dagster-graphql**: `python_modules/dagster-graphql`
**dagster-pipes**: `python_modules/dagster-pipes`
**dagster-webserver**: `python_modules/dagster-webserver`
**dagit**: `python_modules/dagit`

## test packages

**automation**: `python_modules/automation`
**dagster-test**: `python_modules/dagster-test`

## cloud platforms

**dagster-aws**: `python_modules/libraries/dagster-aws`
**dagster-azure**: `python_modules/libraries/dagster-azure`
**dagster-gcp**: `python_modules/libraries/dagster-gcp`
**dagster-gcp-pandas**: `python_modules/libraries/dagster-gcp-pandas`
**dagster-gcp-pyspark**: `python_modules/libraries/dagster-gcp-pyspark`

## container orchestration

**dagster-k8s**: `python_modules/libraries/dagster-k8s`
**dagster-docker**: `python_modules/libraries/dagster-docker`
**dagster-celery**: `python_modules/libraries/dagster-celery`
**dagster-celery-docker**: `python_modules/libraries/dagster-celery-docker`
**dagster-celery-k8s**: `python_modules/libraries/dagster-celery-k8s`

## data processing

**dagster-dask**: `python_modules/libraries/dagster-dask`
**dagster-spark**: `python_modules/libraries/dagster-spark`
**dagster-pyspark**: `python_modules/libraries/dagster-pyspark`
**dagster-databricks**: `python_modules/libraries/dagster-databricks`

## databases

**dagster-postgres**: `python_modules/libraries/dagster-postgres`
**dagster-mysql**: `python_modules/libraries/dagster-mysql`
**dagster-duckdb**: `python_modules/libraries/dagster-duckdb`
**dagster-duckdb-pandas**: `python_modules/libraries/dagster-duckdb-pandas`
**dagster-duckdb-polars**: `python_modules/libraries/dagster-duckdb-polars`
**dagster-duckdb-pyspark**: `python_modules/libraries/dagster-duckdb-pyspark`

## data warehouses

**dagster-snowflake**: `python_modules/libraries/dagster-snowflake`
**dagster-snowflake-pandas**: `python_modules/libraries/dagster-snowflake-pandas`
**dagster-snowflake-polars**: `python_modules/libraries/dagster-snowflake-polars`
**dagster-snowflake-pyspark**: `python_modules/libraries/dagster-snowflake-pyspark`

## data lakes

**dagster-deltalake**: `python_modules/libraries/dagster-deltalake`
**dagster-deltalake-pandas**: `python_modules/libraries/dagster-deltalake-pandas`
**dagster-deltalake-polars**: `python_modules/libraries/dagster-deltalake-polars`

## elt tools

**dagster-dbt**: `python_modules/libraries/dagster-dbt`
**dagster-airbyte**: `python_modules/libraries/dagster-airbyte`
**dagster-fivetran**: `python_modules/libraries/dagster-fivetran`
**dagster-sling**: `python_modules/libraries/dagster-sling`
**dagster-dlt**: `python_modules/libraries/dagster-dlt`
**dagster-embedded-elt**: `python_modules/libraries/dagster-embedded-elt`

## migration tools

**dagster-airflow**: `python_modules/libraries/dagster-airflow`
**dagster-airlift**: `python_modules/libraries/dagster-airlift`

## data processing libraries

**dagster-pandas**: `python_modules/libraries/dagster-pandas`
**dagster-pandera**: `python_modules/libraries/dagster-pandera`
**dagstermill**: `python_modules/libraries/dagstermill`
**dagster-ge**: `python_modules/libraries/dagster-ge`

## bi tools

**dagster-looker**: `python_modules/libraries/dagster-looker`
**dagster-tableau**: `python_modules/libraries/dagster-tableau`
**dagster-powerbi**: `python_modules/libraries/dagster-powerbi`
**dagster-sigma**: `python_modules/libraries/dagster-sigma`
**dagster-omni**: `python_modules/libraries/dagster-omni`
**dagster-polytomic**: `python_modules/libraries/dagster-polytomic`

## ml platforms

**dagster-mlflow**: `python_modules/libraries/dagster-mlflow`
**dagster-wandb**: `python_modules/libraries/dagster-wandb`
**dagster-openai**: `python_modules/libraries/dagster-openai`

## monitoring

**dagster-datadog**: `python_modules/libraries/dagster-datadog`
**dagster-prometheus**: `python_modules/libraries/dagster-prometheus`
**dagster-papertrail**: `python_modules/libraries/dagster-papertrail`
**dagster-pagerduty**: `python_modules/libraries/dagster-pagerduty`

## notifications

**dagster-slack**: `python_modules/libraries/dagster-slack`
**dagster-msteams**: `python_modules/libraries/dagster-msteams`
**dagster-twilio**: `python_modules/libraries/dagster-twilio`

## utilities

**dagster-shared**: `python_modules/libraries/dagster-shared`
**dagster-ssh**: `python_modules/libraries/dagster-ssh`
**dagster-github**: `python_modules/libraries/dagster-github`
**dagster-datahub**: `python_modules/libraries/dagster-datahub`
**dagster-census**: `python_modules/libraries/dagster-census`
**dagster-hightouch**: `python_modules/libraries/dagster-hightouch`
**dagster-managed-elements**: `python_modules/libraries/dagster-managed-elements`

## cli tools

**dagster-cloud-cli**: `python_modules/libraries/dagster-cloud-cli`
**dagster-dg-cli**: `python_modules/libraries/dagster-dg-cli`
**dagster-dg-core**: `python_modules/libraries/dagster-dg-core`
**create-dagster**: `python_modules/libraries/create-dagster`

## development packages

**kitchen-sink** (airlift): `python_modules/libraries/dagster-airlift/kitchen-sink`
**kitchen-sink** (dbt): `python_modules/libraries/dagster-dbt/kitchen-sink`
**perf-harness**: `python_modules/libraries/dagster-airlift/perf-harness`

## quick lookup patterns

All paths are relative to the repository root and follow these patterns:

- Core: `python_modules/{package-name}`
- Libraries: `python_modules/libraries/{package-name}`
- Testing: Most packages have `{package-name}_tests/` subdirectories
