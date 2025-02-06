---
title: "Kind tags"
description: "Use kind tags to easily categorize assets within you Dagster project."
sidebar_position: 200
---

Kind tags can help you quickly identify the underlying system or technology used for a given asset in the Dagster UI. These tags allow you to organize assets within a Dagster project and can be used to filter or search across all your assets.

## Adding kinds to an asset

You may add up to three kinds to the `kinds` argument of an <PyObject section="assets" module="dagster" object="asset" decorator />, which can be useful to represent multiple technologies or systems that an asset is associated with. For example, an asset which is built by Python code and stored in Snowflake can be tagged with both `python` and `snowflake` kinds:

{/* TODO convert to <CodeExample> */}
```python file=/concepts/metadata-tags/asset_kinds.py
from dagster import asset


@asset(kinds={"python", "snowflake"})
def my_asset():
    pass
```

Kinds can also be specified on an <PyObject section="assets" module="dagster" object="AssetSpec" />, for use in multi-assets:

```python file=/concepts/metadata-tags/asset_kinds_multi.py
from dagster import AssetSpec, multi_asset


@multi_asset(
    specs=[
        AssetSpec("foo", kinds={"python", "snowflake"}),
        AssetSpec("bar", kinds={"python", "postgres"}),
    ]
)
def my_multi_asset():
    pass
```

On the backend, these kind inputs are stored as tags on the asset. For more information, see [Tags](/guides/build/assets/metadata-and-tags/index.md#tags).

When viewing the asset in the lineage view, the attached kinds will be visible at the bottom the asset.

<img
  src="/images/guides/build/assets/metadata-tags/kinds/kinds.svg"
  alt="Asset in lineage view with attached kind tags"
/>

## Adding compute kinds to assets

:::warning

Using `compute_kind` has been superseded by the `kinds` argument. We recommend using the `kinds` argument instead.

:::

You can add a single compute kind to any asset by providing a value to the `compute_kind` argument.

```python
@asset(compute_kind="dbt")
def my_asset():
    pass
```

## Supported Icons

Some kinds are given a branded icon in the UI. We currently support nearly 200 unique technology icons.

| Value               | Icon                                                                                                               |
| ------------------- | ------------------------------------------------------------------------------------------------------------------ |
| `airbyte`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-airbyte-color.svg" width={20} height={20} />           |
| `airflow`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-airflow-color.svg" width={20} height={20} />           |
| `airliftmapped`     | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-airflow-color.svg" width={20} height={20} />           |
| `airtable`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-airtable-color.svg" width={20} height={20} />          |
| `athena`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-aws-color.svg" width={20} height={20} />               |
| `atlan`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-atlan-color.svg" width={20} height={20} />             |
| `aws`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-aws-color.svg" width={20} height={20} />               |
| `awsstepfunction`   | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-stepfunctions-color.svg" width={20} height={20} />     |
| `awsstepfunctions`  | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-stepfunctions-color.svg" width={20} height={20} />     |
| `axioma`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-axioma-color.svg" width={20} height={20} />            |
| `azure`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-azure-color.svg" width={20} height={20} />             |
| `azureml`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-azureml-color.svg" width={20} height={20} />           |
| `bigquery`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-bigquery-color.svg" width={20} height={20} />          |
| `cassandra`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-cassandra-color.svg" width={20} height={20} />         |
| `catboost`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-catboost-color.svg" width={20} height={20} />          |
| `celery`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-celery-color.svg" width={20} height={20} />            |
| `census`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-census-color.svg" width={20} height={20} />            |
| `chalk`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-chalk-color.svg" width={20} height={20} />             |
| `claude`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-claude-color.svg" width={20} height={20} />            |
| `clickhouse`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-clickhouse-color.svg" width={20} height={20} />        |
| `cockroachdb`       | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-cockroachdb-color.svg" width={20} height={20} />       |
| `collibra`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-collibra-color.svg" width={20} height={20} />          |
| `cplus`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-cplus-color.svg" width={20} height={20} />             |
| `cplusplus`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-cplus-color.svg" width={20} height={20} />             |
| `csharp`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-csharp-color.svg" width={20} height={20} />            |
| `cube`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-cube-color.svg" width={20} height={20} />              |
| `dask`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-dask-color.svg" width={20} height={20} />              |
| `databricks`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-databricks-color.svg" width={20} height={20} />        |
| `datadog`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-datadog-color.svg" width={20} height={20} />           |
| `datahub`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-datahub-color.svg" width={20} height={20} />           |
| `db2`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-db2-color.svg" width={20} height={20} />               |
| `dbt`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-dbt-color.svg" width={20} height={20} />               |
| `deltalake`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-deltalake-color.svg" width={20} height={20} />         |
| `denodo`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-denodo-color.svg" width={20} height={20} />            |
| `discord`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-discord-color.svg" width={20} height={20} />           |
| `dlt`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-dlthub-color.svg" width={20} height={20} />            |
| `dlthub`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-dlthub-color.svg" width={20} height={20} />            |
| `docker`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-docker-color.svg" width={20} height={20} />            |
| `doris`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-doris-color.svg" width={20} height={20} />             |
| `druid`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-druid-color.svg" width={20} height={20} />             |
| `duckdb`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-duckdb-color.svg" width={20} height={20} />            |
| `elasticsearch`     | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-elasticsearch-color.svg" width={20} height={20} />     |
| `excel`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-excel-color.svg" width={20} height={20} />             |
| `facebook`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-facebook-color.svg" width={20} height={20} />          |
| `fivetran`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-fivetran-color.svg" width={20} height={20} />          |
| `flink`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-flink-color.svg" width={20} height={20} />             |
| `gcp`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-googlecloud-color.svg" width={20} height={20} />       |
| `gcs`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-gcs-color.svg" width={20} height={20} />               |
| `gemini`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-gemini-color.svg" width={20} height={20} />            |
| `github`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-github-color.svg" width={20} height={20} />            |
| `gitlab`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-gitlab-color.svg" width={20} height={20} />            |
| `go`                | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-go-color.svg" width={20} height={20} />                |
| `google`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-google-color.svg" width={20} height={20} />            |
| `googlecloud`       | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-googlecloud-color.svg" width={20} height={20} />       |
| `googledrive`       | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-googledrive-color.svg" width={20} height={20} />       |
| `googlesheets`      | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-googlesheets-color.svg" width={20} height={20} />      |
| `graphql`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-graphql-color.svg" width={20} height={20} />           |
| `greatexpectations` | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-greatexpectations-color.svg" width={20} height={20} /> |
| `hackernews`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-hackernews-color.svg" width={20} height={20} />        |
| `hackernewsapi`     | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-hackernews-color.svg" width={20} height={20} />        |
| `hadoop`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-hadoop-color.svg" width={20} height={20} />            |
| `hashicorp`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-hashicorp-color.svg" width={20} height={20} />         |
| `hex`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-hex-color.svg" width={20} height={20} />               |
| `hightouch`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-hightouch-color.svg" width={20} height={20} />         |
| `hudi`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-hudi-color.svg" width={20} height={20} />              |
| `huggingface`       | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-huggingface-color.svg" width={20} height={20} />       |
| `huggingfaceapi`    | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-huggingface-color.svg" width={20} height={20} />       |
| `iceberg`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-iceberg-color.svg" width={20} height={20} />           |
| `icechunk`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-icechunk-color.svg" width={20} height={20} />          |
| `impala`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-impala-color.svg" width={20} height={20} />            |
| `instagram`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-instagram-color.svg" width={20} height={20} />         |
| `ipynb`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-jupyter-color.svg" width={20} height={20} />           |
| `java`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-java-color.svg" width={20} height={20} />              |
| `javascript`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-javascript-color.svg" width={20} height={20} />        |
| `jupyter`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-jupyter-color.svg" width={20} height={20} />           |
| `k8s`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-k8s-color.svg" width={20} height={20} />               |
| `kafka`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-kafka-color.svg" width={20} height={20} />             |
| `kubernetes`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-k8s-color.svg" width={20} height={20} />               |
| `lakefs`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-lakefs-color.svg" width={20} height={20} />            |
| `lightgbm`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-lightgbm-color.svg" width={20} height={20} />          |
| `linear`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-linear-color.svg" width={20} height={20} />            |
| `linkedin`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-linkedin-color.svg" width={20} height={20} />          |
| `llama`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-llama-color.svg" width={20} height={20} />             |
| `looker`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-looker-color.svg" width={20} height={20} />            |
| `mariadb`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-mariadb-color.svg" width={20} height={20} />           |
| `matplotlib`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-matplotlib-color.svg" width={20} height={20} />        |
| `meltano`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-meltano-color.svg" width={20} height={20} />           |
| `meta`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-meta-color.svg" width={20} height={20} />              |
| `metabase`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-metabase-color.svg" width={20} height={20} />          |
| `microsoft`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-microsoft-color.svg" width={20} height={20} />         |
| `minio`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-minio-color.svg" width={20} height={20} />             |
| `mistral`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-mistral-color.svg" width={20} height={20} />           |
| `mlflow`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-mlflow-color.svg" width={20} height={20} />            |
| `modal`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-modal-color.svg" width={20} height={20} />             |
| `mongodb`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-mongodb-color.svg" width={20} height={20} />           |
| `montecarlo`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-montecarlo-color.svg" width={20} height={20} />        |
| `mysql`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-mysql-color.svg" width={20} height={20} />             |
| `net`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-microsoft-color.svg" width={20} height={20} />         |
| `noteable`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-noteable-color.svg" width={20} height={20} />          |
| `notion`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-notion-color.svg" width={20} height={20} />            |
| `numpy`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-numpy-color.svg" width={20} height={20} />             |
| `omni`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-omni-color.svg" width={20} height={20} />              |
| `openai`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-openai-color.svg" width={20} height={20} />            |
| `openmetadata`      | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-openmetadata-color.svg" width={20} height={20} />      |
| `optuna`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-optuna-color.svg" width={20} height={20} />            |
| `oracle`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-oracle-color.svg" width={20} height={20} />            |
| `pagerduty`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-pagerduty-color.svg" width={20} height={20} />         |
| `pandas`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-pandas-color.svg" width={20} height={20} />            |
| `pandera`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-pandera-color.svg" width={20} height={20} />           |
| `papermill`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-papermill-color.svg" width={20} height={20} />         |
| `papertrail`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-papertrail-color.svg" width={20} height={20} />        |
| `parquet`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-parquet-color.svg" width={20} height={20} />           |
| `pinot`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-pinot-color.svg" width={20} height={20} />             |
| `plotly`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-plotly-color.svg" width={20} height={20} />            |
| `plural`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-plural-color.svg" width={20} height={20} />            |
| `polars`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-polars-color.svg" width={20} height={20} />            |
| `postgres`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-postgres-color.svg" width={20} height={20} />          |
| `postgresql`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-postgres-color.svg" width={20} height={20} />          |
| `powerbi`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-powerbi-color.svg" width={20} height={20} />           |
| `prefect`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-prefect-color.svg" width={20} height={20} />           |
| `presto`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-presto-color.svg" width={20} height={20} />            |
| `pulsar`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-pulsar-color.svg" width={20} height={20} />            |
| `pyspark`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-spark-color.svg" width={20} height={20} />             |
| `python`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-python-color.svg" width={20} height={20} />            |
| `pytorch`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-pytorch-color.svg" width={20} height={20} />           |
| `pytorchlightning`  | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-pytorchlightning-color.svg" width={20} height={20} />  |
| `r`                 | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-r-color.svg" width={20} height={20} />                 |
| `rabbitmq`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-rabbitmq-color.svg" width={20} height={20} />          |
| `ray`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-ray-color.svg" width={20} height={20} />               |
| `react`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-react-color.svg" width={20} height={20} />             |
| `reddit`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-reddit-color.svg" width={20} height={20} />            |
| `redis`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-redis-color.svg" width={20} height={20} />             |
| `redpanda`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-redpanda-color.svg" width={20} height={20} />          |
| `redshift`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-redshift-color.svg" width={20} height={20} />          |
| `rockset`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-rockset-color.svg" width={20} height={20} />           |
| `rust`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-rust-color.svg" width={20} height={20} />              |
| `s3`                | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-s3-color.svg" width={20} height={20} />                |
| `sagemaker`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-sagemaker-color.svg" width={20} height={20} />         |
| `salesforce`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-salesforce-color.svg" width={20} height={20} />        |
| `scala`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-scala-color.svg" width={20} height={20} />             |
| `scikitlearn`       | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-scikitlearn-color.svg" width={20} height={20} />       |
| `scipy`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-scipy-color.svg" width={20} height={20} />             |
| `scylladb`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-scylladb-color.svg" width={20} height={20} />          |
| `sdf`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-sdf-color.svg" width={20} height={20} />               |
| `secoda`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-secoda-color.svg" width={20} height={20} />            |
| `segment`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-segment-color.svg" width={20} height={20} />           |
| `sharepoint`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-sharepoint-color.svg" width={20} height={20} />        |
| `shell`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-shell-color.svg" width={20} height={20} />             |
| `shopify`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-shopify-color.svg" width={20} height={20} />           |
| `sigma`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/sigma.svg" width={20} height={20} />                        |
| `slack`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-slack-color.svg" width={20} height={20} />             |
| `sling`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-sling-color.svg" width={20} height={20} />             |
| `snowflake`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-snowflake-color.svg" width={20} height={20} />         |
| `snowpark`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-snowflake-color.svg" width={20} height={20} />         |
| `soda`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-soda-color.svg" width={20} height={20} />              |
| `spanner`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-spanner-color.svg" width={20} height={20} />           |
| `spark`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-spark-color.svg" width={20} height={20} />             |
| `sql`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-sql-color.svg" width={20} height={20} />               |
| `sqlite`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-sqlite-color.svg" width={20} height={20} />            |
| `sqlmesh`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-sqlmesh-color.svg" width={20} height={20} />           |
| `sqlserver`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-sqlserver-color.svg" width={20} height={20} />         |
| `starrocks`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-starrocks-color.svg" width={20} height={20} />         |
| `stepfunction`      | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-stepfunctions-color.svg" width={20} height={20} />     |
| `stepfunctions`     | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-stepfunctions-color.svg" width={20} height={20} />     |
| `stitch`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-stitch-color.svg" width={20} height={20} />            |
| `stripe`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-stripe-color.svg" width={20} height={20} />            |
| `superset`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-superset-color.svg" width={20} height={20} />          |
| `tableau`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-tableau-color.svg" width={20} height={20} />           |
| `teams`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-teams-color.svg" width={20} height={20} />             |
| `tecton`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-tecton-color.svg" width={20} height={20} />            |
| `tensorflow`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-tensorflow-color.svg" width={20} height={20} />        |
| `teradata`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-teradata-color.svg" width={20} height={20} />          |
| `thoughtspot`       | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-thoughtspot-color.svg" width={20} height={20} />       |
| `trino`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-trino-color.svg" width={20} height={20} />             |
| `twilio`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-twilio-color.svg" width={20} height={20} />            |
| `twitter`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-x-color.svg" width={20} height={20} />                 |
| `typescript`        | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-typescript-color.svg" width={20} height={20} />        |
| `vercel`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-vercel-color.svg" width={20} height={20} />            |
| `wandb`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-w&b-color.svg" width={20} height={20} />               |
| `x`                 | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-x-color.svg" width={20} height={20} />                 |
| `xgboost`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-xgboost-color.svg" width={20} height={20} />           |
| `youtube`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/tool-youtube-color.svg" width={20} height={20} />           |
| `bronze`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/medallion-bronze-color.svg" width={20} height={20} />       |
| `silver`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/medallion-silver-color.svg" width={20} height={20} />       |
| `gold`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/medallion-gold-color.svg" width={20} height={20} />         |
| `dag`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/dag.svg" width={20} height={20} />                          |
| `task`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/task.svg" width={20} height={20} />                         |
| `table`             | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/table.svg" width={20} height={20} />                        |
| `view`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/view.svg" width={20} height={20} />                         |
| `dataset`           | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/table.svg" width={20} height={20} />                        |
| `semanticmodel`     | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/table.svg" width={20} height={20} />                        |
| `source`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/source.svg" width={20} height={20} />                       |
| `seed`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/seed.svg" width={20} height={20} />                         |
| `file`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/file.svg" width={20} height={20} />                         |
| `dashboard`         | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/dashboard.svg" width={20} height={20} />                    |
| `report`            | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/notebook.svg" width={20} height={20} />                     |
| `notebook`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/notebook.svg" width={20} height={20} />                     |
| `workbook`          | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/dashboard.svg" width={20} height={20} />                    |
| `csv`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/csv.svg" width={20} height={20} />                          |
| `pdf`               | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/pdf.svg" width={20} height={20} />                          |
| `yaml`              | <img src="/images/guides/build/assets/metadata-tags/kinds/icons/yaml.svg" width={20} height={20} />                         |

## Requesting additional icons

The kinds icon pack is open source and anyone can [contribute new icons](/about/contributing) to the public repo or request a new icon by [filing an issue](https://github.com/dagster-io/dagster/issues/new?assignees=&labels=type%3A+feature-request&projects=&template=request_a_feature.ym). Custom icons per deployment are not currently supported.
