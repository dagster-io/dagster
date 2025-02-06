---
title: "dagster-snowflake integration reference"
description: Store your Dagster assets in Snowflak
sidebar_position: 300
---

This reference page provides information for working with [`dagster-snowflake`](/api/python-api/libraries/dagster-snowflake) features that are not covered as part of the Snowflake & Dagster tutorials ([resources](using-snowflake-with-dagster), [I/O managers](using-snowflake-with-dagster-io-managers)).

## Authenticating using a private key

In addition to password-based authentication, you can authenticate with Snowflake using a key pair. To set up private key authentication for your Snowflake account, see the instructions in the [Snowflake docs](https://docs.snowflake.com/en/user-guide/key-pair-auth.html#configuring-key-pair-authentication).

Currently, the Dagster's Snowflake integration only supports encrypted private keys. You can provide the private key directly to the Snowflake resource or I/O manager, or via a file containing the private key.

<Tabs>
<TabItem value="Resources" label="Resources">

**Directly to the resource**

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/private_key_auth_resource.py" startAfter="start_direct_key" endBefore="end_direct_key" />

**Via a file**

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/private_key_auth_resource.py" startAfter="start_key_file" endBefore="end_key_file" />

</TabItem>
<TabItem value="I/O managers" label="I/O managers">

**Directly to the I/O manager**

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/private_key_auth_io_manager.py" startAfter="start_direct_key" endBefore="end_direct_key" />

**Via a file**

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/private_key_auth_io_manager.py" startAfter="start_key_file" endBefore="end_key_file" />

</TabItem>
</Tabs>

## Using the Snowflake resource

### Executing custom SQL commands

Using a [Snowflake resource](/api/python-api/libraries/dagster-snowflake#resource), you can execute custom SQL queries on a Snowflake database:

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/resource.py" startAfter="start" endBefore="end" />

Let's review what's happening in this example:

- Attached the `SnowflakeResource` to the `small_petals` asset
- Used the `get_connection` context manager method of the Snowflake resource to get a [`snowflake.connector.Connection`](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api#object-connection) object
- Used the connection to execute a custom SQL query against the `IRIS_DATASET` table created in [Step 2](using-snowflake-with-dagster#step-2-create-tables-in-snowflake) of the [Snowflake resource tutorial](using-snowflake-with-dagster)

For more information on the Snowflake resource, including additional configuration settings, see the <PyObject section="libraries" object="SnowflakeResource" module="dagster_snowflake" /> API docs.

## Using the Snowflake I/O manager

### Selecting specific columns in a downstream asset

Sometimes you may not want to fetch an entire table as the input to a downstream asset. With the Snowflake I/O manager, you can select specific columns to load by supplying metadata on the downstream asset.

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/downstream_columns.py" />

In this example, we only use the columns containing sepal data from the `IRIS_DATASET` table created in [Step 2](using-snowflake-with-dagster-io-managers#store-a-dagster-asset-as-a-table-in-snowflake) of the [Snowflake I/O manager tutorial](using-snowflake-with-dagster-io-managers). Fetching the entire table would be unnecessarily costly, so to select specific columns, we can add metadata to the input asset. We do this in the `metadata` parameter of the `AssetIn` that loads the `iris_dataset` asset in the `ins` parameter. We supply the key `columns` with a list of names of the columns we want to fetch.

When Dagster materializes `sepal_data` and loads the `iris_dataset` asset using the Snowflake I/O manager, it will only fetch the `sepal_length_cm` and `sepal_width_cm` columns of the `FLOWERS.IRIS.IRIS_DATASET` table and pass them to `sepal_data` as a Pandas DataFrame.

### Storing partitioned assets

The Snowflake I/O manager supports storing and loading partitioned data. In order to correctly store and load data from the Snowflake table, the Snowflake I/O manager needs to know which column contains the data defining the partition bounds. The Snowflake I/O manager uses this information to construct the correct queries to select or replace the data. In the following sections, we describe how the I/O manager constructs these queries for different types of partitions.

<Tabs>
<TabItem value="Statically-partitioned assets" label="Statically-partitioned assets">

To store statically-partitioned assets in Snowflake, specify `partition_expr` metadata on the asset to tell the Snowflake I/O manager which column contains the partition data:

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/static_partition.py" />

Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the partition in the downstream asset. When loading a static partition (or multiple static partitions), the following statement is used:

```sql
SELECT *
 WHERE [partition_expr] in ([selected partitions])
```

When the `partition_expr` value is injected into this statement, the resulting SQL query must follow Snowflake's SQL syntax. Refer to the [Snowflake documentation](https://docs.snowflake.com/en/sql-reference/constructs) for more information.

{/* TODO fix link: When materializing the above assets, a partition must be selected, as described in [Materializing partitioned assets](/concepts/partitions-schedules-sensors/partitioning-assets#materializing-partitioned-assets).*/} When materializing the above assets, a partition must be selected. In this example, the query used when materializing the `Iris-setosa` partition of the above assets would be:

```sql
SELECT *
 WHERE SPECIES in ('Iris-setosa')
```

</TabItem>
<TabItem value="Time-partitioned assets">

Like statically-partitioned assets, you can specify `partition_expr` metadata on the asset to tell the Snowflake I/O manager which column contains the partition data:

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/time_partition.py" startAfter="start_example" endBefore="end_example" />

Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the correct partition in the downstream asset. When loading a dynamic partition, the following statement is used:

```sql
SELECT *
 WHERE [partition_expr] >= [partition_start]
   AND [partition_expr] < [partition_end]
```

When the `partition_expr` value is injected into this statement, the resulting SQL query must follow Snowflake's SQL syntax. Refer to the [Snowflake documentation](https://docs.snowflake.com/en/sql-reference/constructs) for more information.

{/* TODO fix link: When materializing the above assets, a partition must be selected, as described in [Materializing partitioned assets](/concepts/partitions-schedules-sensors/partitioning-assets#materializing-partitioned-assets). */} When materializing the above assets, a partition must be selected. The `[partition_start]` and `[partition_end]` bounds are of the form `YYYY-MM-DD HH:MM:SS`. In this example, the query when materializing the `2023-01-02` partition of the above assets would be:

```sql
SELECT *
 WHERE TO_TIMESTAMP(TIME::INT) >= '2023-01-02 00:00:00'
   AND TO_TIMESTAMP(TIME::INT) < '2023-01-03 00:00:00'
```

In this example, the data in the `TIME` column are integers, so the `partition_expr` metadata includes a SQL statement to convert integers to timestamps. A full list of Snowflake functions can be found [here](https://docs.snowflake.com/en/sql-reference/functions-all).

</TabItem>
<TabItem value="Multi-partitioned assets">

The Snowflake I/O manager can also store data partitioned on multiple dimensions. To do this, you must specify the column for each partition as a dictionary of `partition_expr` metadata:

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/multi_partition.py" startAfter="start_example" endBefore="end_example" />

Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the correct partition in a downstream asset. For multi-partitions, Dagster concatenates the `WHERE` statements described in the above sections to craft the correct `SELECT` statement.

{/* TODO fix link: When materializing the above assets, a partition must be selected, as described in [Materializing partitioned assets](/concepts/partitions-schedules-sensors/partitioning-assets#materializing-partitioned-assets). */} When materializing the above assets, a partition must be selected. For example, when materializing the `2023-01-02|Iris-setosa` partition of the above assets, the following query will be used:

```sql
SELECT *
 WHERE SPECIES in ('Iris-setosa')
   AND TO_TIMESTAMP(TIME::INT) >= '2023-01-02 00:00:00'
   AND TO_TIMESTAMP(TIME::INT) < '2023-01-03 00:00:00'
```

</TabItem>
</Tabs>

### Storing tables in multiple schemas

If you want to have different assets stored in different Snowflake schemas, the Snowflake I/O manager allows you to specify the schema in a few ways.

You can specify the default schema where data will be stored as configuration to the I/O manager, like we did in [Step 1](using-snowflake-with-dagster-io-managers#step-1-configure-the-snowflake-io-manager) of the [Snowflake I/O manager tutorial](using-snowflake-with-dagster-io-managers).

To store assets in different schemas, specify the schema as metadata:

{/* TODO add dedent=4 prop to CodeExample below */}
<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/schema.py" startAfter="start_metadata" endBefore="end_metadata" />

You can also specify the schema as part of the asset's asset key:

{/* TODO add dedent=4 prop to CodeExample below */}
<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/schema.py" startAfter="start_asset_key" endBefore="end_asset_key" />

In this example, the `iris_dataset` asset will be stored in the `IRIS` schema, and the `daffodil_dataset` asset will be found in the `DAFFODIL` schema.

:::note

  The schema is determined in this order:
  <ol>
    <li>If the schema is set via metadata, that schema will be used</li>
    <li>
      Otherwise, the schema set as configuration on the I/O manager will be used
    </li>
    <li>
      Otherwise, if there is a <code>key_prefix</code>, that schema will be used
    </li>
    <li>
      If none of the above are provided, the default schema will be <code>PUBLIC</code>
    </li>
  </ol>

:::

### Storing timestamp data in Pandas DataFrames

When storing a Pandas DataFrame with the Snowflake I/O manager, the I/O manager will check if timestamp data has a timezone attached, and if not, **it will assign the UTC timezone**. In Snowflake, you will see the timestamp data stored as the `TIMESTAMP_NTZ(9)` type, as this is the type assigned by the Snowflake Pandas connector.

:::note

Prior to `dagster-snowflake` version `0.19.0` the Snowflake I/O manager converted all timestamp data to strings before loading the data in Snowflake, and did the opposite conversion when fetching a DataFrame from Snowflake. If you have used a version of `dagster-snowflake` prior to version `0.19.0`, see the [Migration Guide](/guides/migrate/version-migration#extension-libraries) for information about migrating database tables.

:::

### Using the Snowflake I/O manager with other I/O managers

You may have assets that you don't want to store in Snowflake. You can provide an I/O manager to each asset using the `io_manager_key` parameter in the `asset` decorator:

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/multiple_io_managers.py" startAfter="start_example" endBefore="end_example" />

In this example, the `iris_dataset` asset uses the I/O manager bound to the key `warehouse_io_manager` and `iris_plots` will use the I/O manager bound to the key `blob_io_manager`. In the <PyObject section="definitions" module="dagster" object="Definitions" /> object, we supply the I/O managers for those keys. When the assets are materialized, the `iris_dataset` will be stored in Snowflake, and `iris_plots` will be saved in Amazon S3.

### Storing and loading PySpark DataFrames in Snowflake

The Snowflake I/O manager also supports storing and loading PySpark DataFrames. To use the <PyObject section="libraries" module="dagster_snowflake_pyspark" object="SnowflakePySparkIOManager" />, first install the package:

```shell
pip install dagster-snowflake-pyspark
```

Then you can use the `SnowflakePySparkIOManager` in your `Definitions` as in [Step 1](using-snowflake-with-dagster-io-managers#step-1-configure-the-snowflake-io-manager) of the [Snowflake I/O manager tutorial](using-snowflake-with-dagster-io-managers).

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/pyspark_configuration.py" startAfter="start_configuration" endBefore="end_configuration" />

:::note

When using the `snowflake_pyspark_io_manager` the `warehouse` configuration is required.

:::

The `SnowflakePySparkIOManager` requires that a `SparkSession` be active and configured with the [Snowflake connector for Spark](https://docs.snowflake.com/en/user-guide/spark-connector.html). You can either create your own `SparkSession` or use the <PyObject section="libraries" module="dagster_spark" object="spark_resource"/>.

<Tabs>
<TabItem value="With the spark_resource">

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/pyspark_with_spark_resource.py" />

</TabItem>
<TabItem value="With your own SparkSession">

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/pyspark_with_spark_session.py" />

</TabItem>
</Tabs>

### Using Pandas and PySpark DataFrames with Snowflake

If you work with both Pandas and PySpark DataFrames and want a single I/O manager to handle storing and loading these DataFrames in Snowflake, you can write a new I/O manager that handles both types. To do this, inherit from the <PyObject section="libraries" module="dagster_snowflake" object="SnowflakeIOManager" /> base class and implement the `type_handlers` and `default_load_type` methods. The resulting I/O manager will inherit the configuration fields of the base `SnowflakeIOManager`.

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/pandas_and_pyspark.py" startAfter="start_example" endBefore="end_example" />
