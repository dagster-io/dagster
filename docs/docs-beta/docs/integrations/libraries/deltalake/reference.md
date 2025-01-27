---
title: "dagster-deltalake integration reference"
description: Store your Dagster assets in Delta Lake
sidebar_position: 200
---

This reference page provides information for working with [`dagster-deltalake`](/api/python-api/libraries/dagster-deltalake) features that are not covered as part of the [Using Delta Lake with Dagster tutorial](using-deltalake-with-dagster).

- [Selecting specific columns in a downstream asset](#selecting-specific-columns-in-a-downstream-asset)
- [Storing partitioned assets](#storing-partitioned-assets)
- [Storing tables in multiple schemas](#storing-tables-in-multiple-schemas)
- [Using the Delta Lake I/O manager with other I/O managers](#using-the-delta-lake-io-manager-with-other-io-managers)
- [Storing and loading PyArrow Tables or Polars DataFrames in Delta Lake](#storing-and-loading-pyarrow-tables-or-polars-dataframes-in-delta-lake)
- [Configuring storage backends](#configuring-storage-backends)

## Selecting specific columns in a downstream asset

Sometimes you may not want to fetch an entire table as the input to a downstream asset. With the Delta Lake I/O manager, you can select specific columns to load by supplying metadata on the downstream asset.

<CodeExample path="docs_snippets/docs_snippets/integrations/deltalake/downstream_columns.py" />

In this example, we only use the columns containing sepal data from the `iris_dataset` table created in [Step 2](using-deltalake-with-dagster#step-2-create-delta-lake-tables) of the [Using Dagster with Delta Lake tutorial](using-deltalake-with-dagster). To select specific columns, we can add metadata to the input asset. We do this in the `metadata` parameter of the `AssetIn` that loads the `iris_dataset` asset in the `ins` parameter. We supply the key `columns` with a list of names of the columns we want to fetch.

When Dagster materializes `sepal_data` and loads the `iris_dataset` asset using the Delta Lake I/O manager, it will only fetch the `sepal_length_cm` and `sepal_width_cm` columns of the `iris/iris_dataset` table and pass them to `sepal_data` as a Pandas DataFrame.

## Storing partitioned assets

The Delta Lake I/O manager supports storing and loading partitioned data. To correctly store and load data from the Delta table, the Delta Lake I/O manager needs to know which column contains the data defining the partition bounds. The Delta Lake I/O manager uses this information to construct the correct queries to select or replace the data.

In the following sections, we describe how the I/O manager constructs these queries for different types of partitions.

:::

For partitioning to work, the partition dimension needs to be one of the partition columns defined on the Delta table. Tables created via the I/O manager will be configured accordingly.

:::

<Tabs>
<TabItem value="Static partitioned assets">

**Storing static partitioned assets**

To store static partitioned assets in your Delta Lake, specify `partition_expr` metadata on the asset to tell the Delta Lake I/O manager which column contains the partition data:

<CodeExample path="docs_snippets/docs_snippets/integrations/deltalake/static_partition.py" startAfter="start_example" endBefore="end_example" />

Dagster uses the `partition_expr` metadata to generate appropriate function parameters when loading the partition in the downstream asset. When loading a static partition this roughly corresponds to the following SQL statement:

```sql
SELECT *
 WHERE [partition_expr] in ([selected partitions])
```

A partition must be selected when materializing the above assets, as described in the [Materializing partitioned assets](/guides/build/partitions-and-backfills/partitioning-assets) documentation. In this example, the query used when materializing the `Iris-setosa` partition of the above assets would be:

```sql
SELECT *
 WHERE species = 'Iris-setosa'
```

</TabItem>
<TabItem value="Time-partitioned assets">

**Storing time-partitioned assets**

Like static partitioned assets, you can specify `partition_expr` metadata on the asset to tell the Delta Lake I/O manager which column contains the partition data:

<CodeExample path="docs_snippets/docs_snippets/integrations/deltalake/time_partition.py" startAfter="start_example" endBefore="end_example" />

Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the correct partition in the downstream asset. When loading a dynamic partition, the following statement is used:

```sql
SELECT *
 WHERE [partition_expr] = [partition_start]
```

A partition must be selected when materializing the above assets, as described in the [Materializing partitioned assets](/guides/build/partitions-and-backfills/partitioning-assets) documentation. The `[partition_start]` and `[partition_end]` bounds are of the form `YYYY-MM-DD HH:MM:SS`. In this example, the query when materializing the `2023-01-02` partition of the above assets would be:

```sql
SELECT *
 WHERE time = '2023-01-02 00:00:00'
```

</TabItem>
<TabItem value="Multi-partitioned assets">

**Storing multi-partitioned assets**

The Delta Lake I/O manager can also store data partitioned on multiple dimensions. To do this, specify the column for each partition as a dictionary of `partition_expr` metadata:

<CodeExample path="docs_snippets/docs_snippets/integrations/deltalake/multi_partition.py" startAfter="start_example" endBefore="end_example" />

Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the correct partition in a downstream asset. For multi-partitions, Dagster concatenates the `WHERE` statements described in the above sections to craft the correct `SELECT` statement.

A partition must be selected when materializing the above assets, as described in the [Materializing partitioned assets](/todo) documentation. For example, when materializing the `2023-01-02|Iris-setosa` partition of the above assets, the following query will be used:

```sql
SELECT *
 WHERE species = 'Iris-setosa'
   AND time = '2023-01-02 00:00:00'
```

</TabItem>
<TabItem value="Dynamic-partitioned assets">
</TabItem>
</Tabs>

## Storing tables in multiple schemas

You may want to have different assets stored in different Delta Lake schemas. The Delta Lake I/O manager allows you to specify the schema in several ways.

If you want all of your assets to be stored in the same schema, you can specify the schema as configuration to the I/O manager, as we did in [Step 1](using-deltalake-with-dagster#step-1-configure-the-delta-lake-io-manager) of the [Using Dagster with Delta Lake tutorial](using-deltalake-with-dagster).

If you want to store assets in different schemas, you can specify the schema as part of the asset's key:

<CodeExample path="docs_snippets/docs_snippets/integrations/deltalake/schema.py" startAfter="start_asset_key" endBefore="end_asset_key" />

In this example, the `iris_dataset` asset will be stored in the `IRIS` schema, and the `daffodil_dataset` asset will be found in the `DAFFODIL` schema.

:::

The two options for specifying schema are mutually exclusive. If you provide `schema` configuration to the I/O manager, you cannot also provide it via the asset key and vice versa. If no `schema` is provided, either from configuration or asset keys, the default schema `public` will be used.

:::

## Using the Delta Lake I/O manager with other I/O managers

You may have assets that you don't want to store in Delta Lake. You can provide an I/O manager to each asset using the `io_manager_key` parameter in the <PyObject section="assets" module="dagster" object="asset" decorator /> decorator:

<CodeExample path="docs_snippets/docs_snippets/integrations/deltalake/multiple_io_managers.py" startAfter="start_example" endBefore="end_example" />

In this example:

- The `iris_dataset` asset uses the I/O manager bound to the key `warehouse_io_manager` and `iris_plots` uses the I/O manager bound to the key `blob_io_manager`
- In the <PyObject section="definitions" module="dagster" object="Definitions" /> object, we supply the I/O managers for those keys
- When the assets are materialized, the `iris_dataset` will be stored in Delta Lake, and `iris_plots` will be saved in Amazon S3

## Storing and loading PyArrow tables or Polars DataFrames in Delta Lake

The Delta Lake I/O manager also supports storing and loading PyArrow and Polars DataFrames.

<Tabs>
<TabItem value="PyArrow Tables">

**Storing and loading PyArrow Tables with Delta Lake**

The `deltalake` package relies heavily on Apache Arrow for efficient data transfer, so PyArrow is natively supported.

You can use the `DeltaLakePyArrowIOManager` in a <PyObject section="definitions" module="dagster" object="Definitions" /> object as in [Step 1](using-deltalake-with-dagster#step-1-configure-the-delta-lake-io-manager) of the [Using Dagster with Delta Lake tutorial](using-deltalake-with-dagster).

<CodeExample path="docs_snippets/docs_snippets/integrations/deltalake/pyarrow_configuration.py" startAfter="start_configuration" endBefore="end_configuration" />

</TabItem>
</Tabs>

## Configuring storage backends

The deltalake library comes with support for many storage backends out of the box. Which exact storage is to be used, is derived from the URL of a storage location.

### S3 compatible storages

The S3 APIs are implemented by a number of providers and it is possible to interact with many of them. However, most S3 implementations do not offer support for atomic operations, which is a requirement for multi writer support. As such some additional setup and configuration is required.

<Tabs>
<TabItem value="Unsafe rename">

In case there will always be only a single writer to a table - this includes no concurrent dagster jobs writing to the same table - you can allow unsafe writes to the table.

```py
from dagster_deltalake import S3Config

config = S3Config(allow_unsafe_rename=True)
```

</TabItem>

<TabItem value="Set-up a locking client">

To use DynamoDB, set the `AWS_S3_LOCKING_PROVIDER` variable to `dynamodb` and create a table named delta_rs_lock_table in Dynamo. An example DynamoDB table creation snippet using the aws CLI follows, and should be customized for your environment’s needs (e.g. read/write capacity modes):

```bash
aws dynamodb create-table --table-name delta_rs_lock_table \
    --attribute-definitions \
        AttributeName=key,AttributeType=S \
    --key-schema \
        AttributeName=key,KeyType=HASH \
    --provisioned-throughput \
        ReadCapacityUnits=10,WriteCapacityUnits=10
```

:::

The delta-rs community is actively working on extending the available options for locking backends. This includes locking backends compatible with Databricks to allow concurrent writes from Databricks and external environments.

:::

</TabItem>

<TabItem value="Cloudflare R2 storage">

Cloudflare R2 storage has built-in support for atomic copy operations. This can be leveraged by sending additional headers with the copy requests.

```py
from dagster_deltalake import S3Config

config = S3Config(copy_if_not_exists="header: cf-copy-destination-if-none-match: *")
```

</TabItem>

</Tabs>

In cases where non-AWS S3 implementations are used, the endpoint URL or the S3 service needs to be provided.

```py
config = S3Config(endpoint="https://<my-s3-endpoint-url>")
```

### Working with locally running storage (emulators)

A common pattern for e.g. integration tests is to run a storage emulator like Azurite, Localstack, o.a. If not configured to use TLS, we need to configure the http client, to allow for http traffic.

```py
config = AzureConfig(use_emulator=True, client=ClientConfig(allow_http=True))
```
