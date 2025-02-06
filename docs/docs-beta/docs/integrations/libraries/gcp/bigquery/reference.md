---
title: "BigQuery integration reference"
description: Store your Dagster assets in BigQuery
sidebar_position: 200
---

This reference page provides information for working with features that are not covered as part of the [Using Dagster with BigQuery tutorial](using-bigquery-with-dagster).

- [Providing credentials as configuration](#providing-credentials-as-configuration)
- [Selecting specific columns in a downstream asset](#selecting-specific-columns-in-a-downstream-asset)
- [Storing partitioned assets](#storing-partitioned-assets)
- [Storing tables in multiple datasets](#storing-tables-in-multiple-datasets)
- [Using the BigQuery I/O manager with other I/O managers](#using-the-bigquery-io-manager-with-other-io-managers)
- [Storing and loading PySpark DataFrames in BigQuery](#storing-and-loading-pyspark-dataframes-in-bigquery)
- [Using Pandas and PySpark DataFrames with BigQuery](#using-pandas-and-pyspark-dataframes-with-bigquery)
- [Executing custom SQL commands with the BigQuery resource](#executing-custom-sql-commands-with-the-bigquery-resource)

## Providing credentials as configuration

In most cases, you will authenticate with Google Cloud Project (GCP) using one of the methods outlined in the [GCP documentation](https://cloud.google.com/docs/authentication/provide-credentials-adc). However, in some cases you may find that you need to provide authentication credentials directly to the BigQuery I/O manager. For example, if you are using [Dagster+ Serverless](/dagster-plus/deployment/deployment-types/serverless) you cannot upload a credential file, so must provide your credentials as an environment variable.

You can provide credentials directly to the BigQuery I/O manager by using the `gcp_credentials` configuration value. The BigQuery I/O manager will create a temporary file to store the credential and will set `GOOGLE_APPLICATION_CREDENTIALS` to point to this file. When the Dagster run is completed, the temporary file is deleted and `GOOGLE_APPLICATION_CREDENTIALS` is unset.

To avoid issues with newline characters in the GCP credential key, you must base64 encode the key. For example, if your GCP key is stored at `~/.gcp/key.json` you can base64 encode the key by using the following shell command:

```shell
cat ~/.gcp/key.json | base64
```

Then you can [set an environment variable](/guides/deploy/using-environment-variables-and-secrets) in your Dagster deployment (for example `GCP_CREDS`) to the encoded key and provide it to the BigQuery I/O manager:

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/config_auth.py" startAfter="start_example" endBefore="end_example" />

## Selecting specific columns in a downstream asset

Sometimes you may not want to fetch an entire table as the input to a downstream asset. With the BigQuery I/O manager, you can select specific columns to load by supplying metadata on the downstream asset.

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/downstream_columns.py" />

In this example, we only use the columns containing sepal data from the `IRIS_DATA` table created in [Step 2: Create tables in BigQuery](using-bigquery-with-dagster#step-2-create-tables-in-bigquery) of the [Using Dagster with BigQuery tutorial](using-bigquery-with-dagster). Fetching the entire table would be unnecessarily costly, so to select specific columns, we can add metadata to the input asset. We do this in the `metadata` parameter of the `AssetIn` that loads the `iris_data` asset in the `ins` parameter. We supply the key `columns` with a list of names of the columns we want to fetch.

When Dagster materializes `sepal_data` and loads the `iris_data` asset using the BigQuery I/O manager, it will only fetch the `sepal_length_cm` and `sepal_width_cm` columns of the `IRIS.IRIS_DATA` table and pass them to `sepal_data` as a Pandas DataFrame.

## Storing partitioned assets

The BigQuery I/O manager supports storing and loading partitioned data. In order to correctly store and load data from the BigQuery table, the BigQuery I/O manager needs to know which column contains the data defining the partition bounds. The BigQuery I/O manager uses this information to construct the correct queries to select or replace the data. In the following sections, we describe how the I/O manager constructs these queries for different types of partitions.

<Tabs>
<TabItem value="Static partitioned assets">

**Storing static partitioned assets**

In order to store static partitioned assets in BigQuery, you must specify `partition_expr` metadata on the asset to tell the BigQuery I/O manager which column contains the partition data:

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/static_partition.py" startAfter="start_example" endBefore="end_example" />

Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the partition in the downstream asset. When loading a static partition, the following statement is used:

```sql
SELECT *
 WHERE [partition_expr] = ([selected partitions])
```

When the `partition_expr` value is injected into this statement, the resulting SQL query must follow BigQuery's SQL syntax. Refer to the [BigQuery documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax) for more information.

When materializing the above assets, a partition must be selected, as described in [Materializing partitioned assets](/todo). In this example, the query used when materializing the `Iris-setosa` partition of the above assets would be:

```sql
SELECT *
 WHERE SPECIES in ('Iris-setosa')
```

</TabItem>
<TabItem value="Time-partitioned assets">

**Storing time partitioned assets**

Like static partitioned assets, you can specify `partition_expr` metadata on the asset to tell the BigQuery I/O manager which column contains the partition data:

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/time_partition.py" startAfter="start_example" endBefore="end_example" />

Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the correct partition in the downstream asset. When loading a dynamic partition, the following statement is used:

```sql
SELECT *
 WHERE [partition_expr] >= [partition_start]
   AND [partition_expr] < [partition_end]
```

When the `partition_expr` value is injected into this statement, the resulting SQL query must follow BigQuery's SQL syntax. Refer to the [BigQuery documentation](https://cloud.google.com/bigquery/docs/reference/standard-sql/query-syntax) for more information.

When materializing the above assets, a partition must be selected, as described in [Materializing partitioned assets](/guides/build/partitions-and-backfills/partitioning-assets). The `[partition_start]` and `[partition_end]` bounds are of the form `YYYY-MM-DD HH:MM:SS`. In this example, the query when materializing the `2023-01-02` partition of the above assets would be:

```sql
SELECT *
 WHERE TIMESTAMP_SECONDS(TIME) >= '2023-01-02 00:00:00'
   AND TIMESTAMP_SECONDS(TIME) < '2023-01-03 00:00:00'
```

In this example, the data in the `TIME` column are integers, so the `partition_expr` metadata includes a SQL statement to convert integers to timestamps. A full list of BigQuery functions can be found [here](https://cloud.google.com/bigquery/docs/reference/standard-sql/functions-and-operators).

</TabItem>
<TabItem value="Multi-partitioned assets">

**Storing multi-partitioned assets**

The BigQuery I/O manager can also store data partitioned on multiple dimensions. To do this, you must specify the column for each partition as a dictionary of `partition_expr` metadata:

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/multi_partition.py" startAfter="start_example" endBefore="end_example" />

Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the correct partition in a downstream asset. For multi-partitions, Dagster concatenates the `WHERE` statements described in the static partition and time-window partition sections to craft the correct `SELECT` statement.

When materializing the above assets, a partition must be selected, as described in [Materializing partitioned assets](/guides/build/partitions-and-backfills/partitioning-assets). For example, when materializing the `2023-01-02|Iris-setosa` partition of the above assets, the following query will be used:

```sql
SELECT *
 WHERE SPECIES in ('Iris-setosa')
   AND TIMESTAMP_SECONDS(TIME) >= '2023-01-02 00:00:00'
   AND TIMESTAMP_SECONDS(TIME) < '2023-01-03 00:00:00'`
```

</TabItem>
</Tabs>

## Storing tables in multiple datasets

You may want to have different assets stored in different BigQuery datasets. The BigQuery I/O manager allows you to specify the dataset in several ways.

You can specify the default dataset where data will be stored as configuration to the I/O manager, like we did in [Step 1: Configure the BigQuery I/O manager](using-bigquery-with-dagster#step-1-configure-the-bigquery-io-manager) of the [Using Dagster with BigQuery tutorial](using-bigquery-with-dagster).

If you want to store assets in different datasets, you can specify the dataset as metadata:

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/dataset.py" startAfter="start_metadata" endBefore="end_metadata" />

You can also specify the dataset as part of the asset's asset key:

{/* TODO add dedent=4 to CodeExample below */}
<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/dataset.py" startAfter="start_asset_key" endBefore="end_asset_key" />

The dataset will be the last prefix before the asset's name. In this example, the `iris_data` asset will be stored in the `IRIS` dataset, and the `daffodil_data` asset will be found in the `DAFFODIL` dataset.

:::note

  The dataset is determined in this order:
  <ol>
    <li>If the dataset is set via metadata, that dataset will be used</li>
    <li>
      Otherwise, the dataset set as configuration on the I/O manager will be
      used
    </li>
    <li>
      Otherwise, if there is a <code>key_prefix</code>, that dataset will be
      used
    </li>
    <li>
      If none of the above are provided, the default dataset will be <code>PUBLIC</code>
    </li>
  </ol>

:::

## Using the BigQuery I/O manager with other I/O managers

You may have assets that you don't want to store in BigQuery. You can provide an I/O manager to each asset using the `io_manager_key` parameter in the `asset` decorator:

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/multiple_io_managers.py" startAfter="start_example" endBefore="end_example" />

In this example, the `iris_data` asset uses the I/O manager bound to the key `warehouse_io_manager` and `iris_plots` will use the I/O manager bound to the key `blob_io_manager`. In the <PyObject section="definitions" module="dagster" object="Definitions" /> object, we supply the I/O managers for those keys. When the assets are materialized, the `iris_data` will be stored in BigQuery, and `iris_plots` will be saved in Amazon S3.

## Storing and loading PySpark DataFrames in BigQuery

The BigQuery I/O manager also supports storing and loading PySpark DataFrames. To use the <PyObject section="libraries" module="dagster_gcp_pyspark" object="BigQueryPySparkIOManager" />, first install the package:

```shell
pip install dagster-gcp-pyspark
```

Then you can use the `gcp_pyspark_io_manager` in your `Definitions` as in [Step 1: Configure the BigQuery I/O manager](using-bigquery-with-dagster#step-1-configure-the-bigquery-io-manager) of the [Using Dagster with BigQuery tutorial](using-bigquery-with-dagster).

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/pyspark_configuration.py" startAfter="start_configuration" endBefore="end_configuration" />

:::note

When using the `BigQueryPySparkIOManager` you may provide the `temporary_gcs_bucket` configuration. This will store the data is a temporary GCS bucket, then all of the data into BigQuery in one operation. If not provided, data will be directly written to BigQuery. If you choose to use a temporary GCS bucket, you must include the [GCS Hadoop connector](https://github.com/GoogleCloudDataproc/hadoop-connectors/tree/master/gcs) in your Spark Session, in addition to the BigQuery connector (described below).

:::

The `BigQueryPySparkIOManager` requires that a `SparkSession` be active and configured with the [BigQuery connector for Spark](https://cloud.google.com/dataproc/docs/tutorials/bigquery-connector-spark-example). You can either create your own `SparkSession` or use the <PyObject section="libraries" module="dagster_spark" object="spark_resource"/>.

<Tabs>
<TabItem value="With the spark_resource">


<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/pyspark_with_spark_resource.py" />

</TabItem>
<TabItem value="With your own SparkSession">


<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/pyspark_with_spark_session.py" />

</TabItem>
</Tabs>

:::note

In order to load data from BigQuery as a PySpark DataFrame, the BigQuery PySpark connector will create a view containing the data. This will result in the creation of a temporary table in your BigQuery dataset. For more details, see the [BigQuery PySpark connector documentation](https://github.com/GoogleCloudDataproc/spark-bigquery-connector#reading-data-from-a-bigquery-query).

:::

## Using Pandas and PySpark DataFrames with BigQuery

If you work with both Pandas and PySpark DataFrames and want a single I/O manager to handle storing and loading these DataFrames in BigQuery, you can write a new I/O manager that handles both types. To do this, inherit from the <PyObject section="libraries" module="dagster_gcp" object="BigQueryIOManager" /> base class and implement the `type_handlers` and `default_load_type` methods. The resulting I/O manager will inherit the configuration fields of the base `BigQueryIOManager`.


<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/pandas_and_pyspark.py" startAfter="start_example" endBefore="end_example" />

## Executing custom SQL commands with the BigQuery resource

In addition to the BigQuery I/O manager, Dagster also provides a BigQuery [resource](/guides/build/external-resources/) for executing custom SQL queries.

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/reference/resource.py" />

In this example, we attach the BigQuery resource to the `small_petals` asset. In the body of the asset function, we use the `get_client` context manager method of the resource to get a [`bigquery.client.Client`](https://cloud.google.com/python/docs/reference/bigquery/latest/google.cloud.bigquery.client.Client). We can use the client to execute a custom SQL query against the `IRIS_DATA` table created in [Step 2: Create tables in BigQuery](using-bigquery-with-dagster#step-2-create-tables-in-bigquery) of the [Using Dagster with BigQuery tutorial](using-bigquery-with-dagster).
