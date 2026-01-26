---
title: Usage
description: This guide walks through common scenarios for using Iceberg with Dagster.
sidebar_position: 4
---

<p>{frontMatter.description}</p>

## Selecting specific columns in a downstream asset

At times, you might prefer not to retrieve an entire table for a downstream asset. The Iceberg I/O manager allows you to load specific columns by providing metadata related to the downstream asset:

<CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/selecting_columns.py" language="python" />

In this example, we focus exclusively on the columns containing sepal data from the `iris_dataset` table. To select specific columns, we can include metadata in the input asset. This is done using the `metadata` parameter of the <PyObject section="assets" module="dagster" object="AssetIn" /> that loads the `iris_dataset` asset within the `ins` parameter. We provide the key `columns` along with a list of the desired column names.

When Dagster materializes `sepal_data` and retrieves the `iris_dataset` asset with the Iceberg I/O manager, it will only extract the `sepal_length_cm` and `sepal_width_cm` columns from the `iris/iris_dataset` table and make them available in `sepal_data` as a pandas DataFrame.

## Storing partitioned assets

The Iceberg I/O manager facilitates the storage and retrieval of partitioned data. To effectively manage data in the Iceberg table, it is essential for the Iceberg I/O manager to identify the column that specifies the partition boundaries. This information allows the I/O manager to formulate the appropriate queries for selecting or replacing data.

Below, we outline how the I/O manager generates these queries for various partition types.

:::info Configuring partition dimensions
For partitioning to function correctly, the partition dimension must correspond to one of the partition columns defined in the Iceberg table. Tables created through the I/O manager will be configured accordingly.
:::

<Tabs>
  <TabItem value="static" label="Static partitions">
    To save static-partitioned assets in your Iceberg table, you need to set the `partition_expr` metadata on the asset. This informs the Iceberg I/O manager which column holds the partition data:

    <CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/storing_static_partitions.py" language="python" />

    Dagster uses the `partition_expr` metadata to create the necessary function parameters when retrieving the partition in the downstream asset. For static partitions, this is roughly equivalent to the following SQL query:

    ```sql
    SELECT *
    WHERE [partition_expr] IN ([selected partitions])
    ```

    A partition must be specified when materializing the above assets, as explained in the [Materializing partitioned assets](/guides/build/partitions-and-backfills/partitioning-assets#materializing-partitioned-assets) documentation. For instance, the query used to materialize the `Iris-setosa` partition of the assets would be:

    ```sql
    SELECT *
    WHERE species = 'Iris-setosa'
    ```

  </TabItem>
  <TabItem value="time" label="Time-based partitions">
    Like static-partitioned assets, you can specify `partition_expr` metadata on the asset to tell the Iceberg I/O manager which column contains the partition data:

    <CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/storing_time_based_partitions.py" language="python" />

    Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the correct partition in the downstream asset. When loading a dynamic partition, the following statement is used:

    ```sql
    SELECT *
    WHERE [partition_expr] = [partition_start]
    ```

    A partition must be selected when materializing the above assets, as described in the [Materializing partitioned assets](/guides/build/partitions-and-backfills/partitioning-assets#materializing-partitioned-assets) documentation. The `[partition_start]` and `[partition_end]` bounds are of the form `YYYY-MM-DD HH:MM:SS`. In this example, the query when materializing the `2023-01-02` partition of the above assets would be:

    ```sql
    SELECT *
    WHERE time = '2023-01-02 00:00:00'
    ```

  </TabItem>
  <TabItem value="multi" label="Multi-dimensional partitions">
    The Iceberg I/O manager can also store data partitioned on multiple dimensions. To do this, specify the column for each partition as a dictionary of `partition_expr` metadata:

    <CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/storing_multi_partitions.py" language="python" />

    Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the correct partition in a downstream asset. For multi-dimensional partitions, Dagster concatenates the `WHERE` statements described in the static and time-based cases to craft the correct `SELECT` statement.

    A partition must be selected when materializing the above assets, as described in the [Materializing partitioned assets](/guides/build/partitions-and-backfills/partitioning-assets#materializing-partitioned-assets) documentation. For example, when materializing the `2023-01-02|Iris-setosa` partition of the above assets, the following query will be used:

    ```sql
    SELECT *
    WHERE species = 'Iris-setosa'
      AND time = '2023-01-02 00:00:00'
    ```

  </TabItem>
</Tabs>

### Partition field naming

Partition fields are named using the column name that they correspond to, with a configurable prefix applied (defaults to `"part-"`). This prefixing is done to comply with changes introduced in pyiceberg 0.10.0 which require that partition field names do not exactly match any existing column names.

For example, an asset that is partitioned using hourly partitions on a column `ingestion_time` will be assigned a corresponding partition field name of `part-ingestion_time`.

The user may configure the prefix in the I/O manager configuration with the `IcebergCatalogConfig`:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/iceberg/partition_field_naming_config.py"
  language="python"
/>

Users may also configure the prefix at launch time using run config if the I/O manager is set up using `configure_at_launch()` (see the [resource configuration docs](/guides/build/external-resources/configuring-resources#configuring-resources-at-launch-time) for more details on this pattern).

## Storing tables in multiple schemas

You may want to have different assets stored in different Iceberg schemas. The Iceberg I/O manager allows you to specify the schema in several ways.

If you want all of your assets to be stored in the same schema, you can specify the schema as configuration to the I/O manager.

If you want to store assets in different schemas, you can specify the schema as part of the asset key:

<CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/handling_multiple_schemas.py" language="python" />

In this example, the `iris_dataset` asset will be stored in the `iris` schema, and the `daffodil_dataset` asset will be found in the `daffodil` schema.

:::info Specifying a schema

The two options for specifying schema are mutually exclusive. If you provide
`schema` configuration to the I/O manager, you cannot also provide
it from the asset key, and vice versa. If no `schema` is provided,
either from configuration or asset keys, the default `public` schema
will be used.

:::

## Using the Iceberg I/O manager with other I/O managers

You may have assets that you don't want to store in Iceberg. You can provide an I/O manager to each asset using the `io_manager_key` parameter in the <PyObject section="assets" module="dagster" object="asset" decorator /> decorator:

<CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/using_multiple_io_managers.py" language="python" />

In the above example:

- The `iris_dataset` asset uses the I/O manager bound to the key `warehouse_io_manager`, and `iris_plots` uses the I/O manager bound to the key `blob_io_manager`.
- We define the I/O managers for those keys in the <PyObject section="definitions" module="dagster" object="Definitions" /> object.
- When the assets are materialized, the `iris_dataset` will be stored in Iceberg, and `iris_plots` will be saved in Amazon S3.

## Using different compute engines to read from and write to Iceberg

`dagster-iceberg` supports several compute engines out-of-the-box. You can [find detailed examples of how to use each engine in the API docs](/integrations/libraries/iceberg/dagster-iceberg#io-managers).

<Tabs>
  <TabItem value="pyarrow" label="PyArrow Tables">
    The `Iceberg` package relies heavily on Apache Arrow for efficient data transfer, so PyArrow is natively supported.

    You can use `PyArrowIcebergIOManager` to read and write iceberg tables:

    <CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/io_manager_pyarrow.py" language="python" />

  </TabItem>
  <TabItem value="pandas" label="Pandas DataFrames">
     You can use `PandasIcebergIOManager` to read and write iceberg tables using Pandas:

    <CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/io_manager_pandas.py" language="python" />

  </TabItem>
  <TabItem value="polars" label="Polars DataFrames">
     You can use the `PolarsIcebergIOManager` to read and write iceberg tables using Polars using a full lazily optimized query engine:

    <CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/io_manager_polars.py" language="python" />

  </TabItem>
  <TabItem value="daft" label="Daft DataFrames">
     You can use the `DaftIcebergIOManager` to read and write iceberg tables using Daft using a full lazily optimized query engine:

    <CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/io_manager_daft.py" language="python" />

  </TabItem>
</Tabs>

## Executing custom SQL commands

In addition to the Iceberg I/O manager, Dagster also provides an <PyObject section="libraries" integration="iceberg" object="resource.IcebergTableResource" module="dagster_iceberg" /> for executing custom SQL queries.

<CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/executing_custom_sql.py" language="python" />

In this example, we attach the resource to the `small_petals` asset. In the body of the asset function, we use the `load()` method to retrieve the Iceberg table object, which can then be used for further processing.

## Configuring table behavior using table properties

PyIceberg tables support table properties to configure table behavior. You can find a [full list of properties in the PyIceberg documentation](https://py.iceberg.apache.org/configuration).

Use asset metadata to set table properties:

<CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/setting_table_properties.py" language="python" />

## Write modes

The Iceberg I/O manager supports three write modes:

- `overwrite` (**default**): every asset materialization will overwrite the backing Iceberg table. Partitioned assets only overwrite partitions of the Iceberg table that were part of the asset materialization.
- `append`: results returned from each asset materialization will be inserted into the backing Iceberg table, respecting partitions when appropriate. **Not currently supported in the Spark I/O manager**.
- `upsert`: asset materialization results will be merged into the backing Iceberg table using [pyiceberg's native implementation](https://py.iceberg.apache.org/api/#upsert), updating any existing records that match on a configurable join key, and inserting records that do not exist in the target table. Insert and update actions can be turned on or off through configuration; for example, you may only want to insert any new records but not update any matching records, or vice versa (see [Using upsert mode](#using-upsert-mode) for usage details). **Not currently supported in the Spark I/O manager**.

The write mode is set using the `write_mode` metadata key, which can be set using asset definition at deployment time, or at runtime within the asset definition body by using output metadata (see the examples in the next section).

### Setting write mode in definition metadata

<CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/write_mode_append.py" language="python" />

### Overriding definition metadata write mode with output metadata

Setting write mode in output metadata overrides any write mode settings in the asset definition metadata:

<CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/write_mode_override.py" language="python" />

### Using upsert mode

**Note:** only supported in non-spark I/O managers

The Iceberg I/O manager supports upsert operations, which allow you to update existing rows and insert new rows in a single operation. This is useful for maintaining slowly changing dimensions or incrementally updating tables.

#### Options

Upsert options can be set at deployment time through asset definition metadata, or dynamically at runtime through output metadata. Upsert options set at runtime through `context.add_output_metadata()` take precedence over those set in definition metadata.

**Required**:

- `join_cols`: **list[str]** - list of columns that make up the join key for the upsert operation

**Optional**:

- `when_matched_update_all`: **bool** - Whether to update rows in the target table that join with the dataframe being upserted (default True)
- `when_not_matched_insert_all`: **bool** - Whether to insert all rows from the upsert dataframe that do not join with the target table (default True)

Any `upsert_options` set when `write_mode` is not set to `upsert` will be ignored, with a debug log message indicating the options were ignored. This allows a user to set the `write_mode` to `upsert` with `upsert_options` in the asset definition metadata while still being able to override the write mode in the output metadata.

To use upsert mode, set the `write_mode` to `"upsert"` and provide `upsert_options` in the asset or output metadata:

<CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/upsert_mode_basic.py" language="python" />

Upsert options set in definition metadata can be overridden at runtime using output metadata:

<CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/upsert_mode_dynamic.py" language="python" />

The `UpsertOptions` `BaseModel` subclass can be used to represent upsert options metadata to provide deployment-time type validation:

<CodeExample path="docs_snippets/docs_snippets/integrations/iceberg/upsert_mode_typed.py" language="python" />

## Allowing updates to schema and partitions

By default, assets will error when you change the partition spec (for example, if you change a partition from hourly to daily) or the schema (for example, when you add a column). You can allow updates to an asset's partition spec and/or schema by setting `partition_spec_update_mode` and/or `schema_update_mode`, respectively, on the asset metadata:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/iceberg/allowing_updates.py"
  startAfter="start_defining_the_asset"
  endBefore="end_defining_the_asset"
/>

## Using the custom I/O manager

The `dagster-iceberg` library leans heavily on Dagster's `DbIOManager` implementation. However, this I/O manager comes with some limitations, such as the lack of support for various [partition mappings](/api/dagster/partitions#partition-mapping). A custom (experimental) `DbIOManager` implementation is available that supports partition mappings as long as any time-based partition is _consecutive_ and static partitions are of string type. You can enable it as follows:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/iceberg/using_custom_io_manager.py"
  startAfter="start_defining_the_io_manager"
  endBefore="end_defining_the_io_manager"
/>

For example, a <PyObject section="partitions" module="dagster" object="MultiToSingleDimensionPartitionMapping" /> is supported:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/iceberg/using_custom_io_manager.py"
  startAfter="start_supported_partition_mapping"
  endBefore="end_supported_partition_mapping"
/>

However, a <PyObject section="partitions" module="dagster" object="SpecificPartitionsPartitionMapping" /> is not, because these dates are not consecutive:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/iceberg/using_custom_io_manager.py"
  startAfter="start_unsupported_partition_mapping"
  endBefore="end_unsupported_partition_mapping"
/>
