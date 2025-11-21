# dagster-iceberg integration reference

This reference page provides information for working with dagster-iceberg.

!!! warning "Iceberg catalog"

    Iceberg requires a catalog backend. A SQLite catalog is used here for illustrative purposes. Do not use this in a production setting. For more information and for catalog configuration settings, visit the [Iceberg documentation](https://py.iceberg.apache.org/configuration/#catalogs).

## Selecting specific columns in a downstream asset

At times, you might prefer not to retrieve an entire table for a downstream asset. The Iceberg I/O manager allows you to load specific columns by providing metadata related to the downstream asset.

```python title="docs/snippets/select_columns.py" linenums="1"
--8<-- "docs/snippets/select_columns.py"
```

In this example, we focus exclusively on the columns containing sepal data from the `iris_dataset` table. To select specific columns, we can include metadata in the input asset. This is done using the `metadata` parameter of the `AssetIn` that loads the `iris_dataset` asset within the `ins` parameter. We provide the key `columns` along with a list of the desired column names.

When Dagster materializes `sepal_data` and retrieves the `iris_dataset` asset via the Iceberg I/O manager, it will only extract the `sepal_length_cm` and `sepal_width_cm` columns from the `iris/iris_dataset` table and deliver them to `sepal_data` as a Pandas DataFrame.

---

## Storing partitioned assets

The Iceberg I/O manager facilitates the storage and retrieval of partitioned data. To effectively manage data in the Iceberg table, it is essential for the Iceberg I/O manager to identify the column that specifies the partition boundaries. This information allows the I/O manager to formulate the appropriate queries for selecting or replacing data.

In the subsequent sections, we will outline how the I/O manager generates these queries for various partition types.

!!! info "Partition dimensions"

    For partitioning to function correctly, the partition dimension must correspond to one of the partition columns defined in the Iceberg table. Tables created through the I/O manager will be set up accordingly.

=== "Storing static partitioned assets"

    To save static partitioned assets in your Iceberg table, you need to set the `partition_expr` metadata on the asset. This informs the Iceberg I/O manager which column holds the partition data:

    ```python title="docs/snippets/partitions_static.py" linenums="1"
    --8<-- "docs/snippets/partitions_static.py"
    ```

    Dagster uses the `partition_expr` metadata to create the necessary function parameters when retrieving the partition in the downstream asset. For static partitions, this is roughly equivalent to the following SQL query:

    ```sql
    SELECT *
    WHERE [partition_expr] in ([selected partitions])
    ```

    A partition must be specified when materializing the above assets, as explained in the [Materializing partitioned assets](/concepts/partitions-schedules-sensors/partitioning-assets#materializing-partitioned-assets) documentation. For instance, the query used to materialize the `Iris-setosa` partition of the assets would be:

    ```sql
    SELECT *
    WHERE species = 'Iris-setosa'
    ```

=== "Storing time-partitioned assets"

    Like static partitioned assets, you can specify `partition_expr` metadata on the asset to tell the Iceberg I/O manager which column contains the partition data:

    ```python title="docs/snippets/partitions_time.py" linenums="1"
    --8<-- "docs/snippets/partitions_time.py"
    ```

    Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the correct partition in the downstream asset. When loading a dynamic partition, the following statement is used:

    ```sql
    SELECT *
    WHERE [partition_expr] = [partition_start]
    ```

    A partition must be selected when materializing the above assets, as described in the [Materializing partitioned assets](/concepts/partitions-schedules-sensors/partitioning-assets#materializing-partitioned-assets) documentation. The `[partition_start]` and `[partition_end]` bounds are of the form `YYYY-MM-DD HH:MM:SS`. In this example, the query when materializing the `2023-01-02` partition of the above assets would be:

    ```sql
    SELECT *
    WHERE time = '2023-01-02 00:00:00'
    ```

=== "Storing multi-partitioned assets"

    The Iceberg I/O manager can also store data partitioned on multiple dimensions. To do this, specify the column for each partition as a dictionary of `partition_expr` metadata:

    ```python title="docs/snippets/partitions_multiple.py" linenums="1"
    --8<-- "docs/snippets/partitions_multiple.py"
    ```

    Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the correct partition in a downstream asset. For multi-partitions, Dagster concatenates the `WHERE` statements described in the above sections to craft the correct `SELECT` statement.

    A partition must be selected when materializing the above assets, as described in the [Materializing partitioned assets](/concepts/partitions-schedules-sensors/partitioning-assets#materializing-partitioned-assets) documentation. For example, when materializing the `2023-01-02|Iris-setosa` partition of the above assets, the following query will be used:

    ```sql
    SELECT *
    WHERE species = 'Iris-setosa'
      AND time = '2023-01-02 00:00:00'
    ```

---

## Storing tables in multiple schemas

You may want to have different assets stored in different Iceberg schemas. The Iceberg I/O manager allows you to specify the schema in several ways.

If you want all of your assets to be stored in the same schema, you can specify the schema as configuration to the I/O manager.

If you want to store assets in different schemas, you can specify the schema as part of the asset's key:

```python title="docs/snippets/multiple_schemas.py" linenums="1"
--8<-- "docs/snippets/multiple_schemas.py"
```

In this example, the `iris_dataset` asset will be stored in the `IRIS` schema, and the `daffodil_dataset` asset will be found in the `DAFFODIL` schema.

!!! info "Specifying a schema"

    The two options for specifying schema are mutually exclusive. If you provide{" "}
    <code>schema</code> configuration to the I/O manager, you cannot also provide
    it via the asset key and vice versa. If no <code>schema</code> is provided,
    either from configuration or asset keys, the default schema{" "}
    <code>public</code> will be used.

---

## Using the Iceberg I/O manager with other I/O managers

You may have assets that you don't want to store in Iceberg. You can provide an I/O manager to each asset using the `io_manager_key` parameter in the <PyObject object="asset" decorator /> decorator:

```python title="docs/snippets/multiple_io_managers.py" linenums="1"
--8<-- "docs/snippets/multiple_io_managers.py"
```

In this example:

- The `iris_dataset` asset uses the I/O manager bound to the key `warehouse_io_manager` and `iris_plots` uses the I/O manager bound to the key `blob_io_manager`
- In the <PyObject object="Definitions" /> object, we supply the I/O managers for those keys
- When the assets are materialized, the `iris_dataset` will be stored in Iceberg, and `iris_plots` will be saved in Amazon S3

---

## Storing and loading PyArrow, Pandas, or Polars DataFrames with Iceberg

The Iceberg I/O manager also supports storing and loading PyArrow and Polars DataFrames.

=== "PyArrow Tables"

    The `Iceberg` package relies heavily on Apache Arrow for efficient data transfer, so PyArrow is natively supported.

    You can use `PyArrowIcebergIOManager` to read and write iceberg tables:

    ```python title="docs/snippets/io_manager_pyarrow.py" linenums="1"
    --8<-- "docs/snippets/io_manager_pyarrow.py"
    ```

=== "Pandas DataFrames"

     You can use `PandasIcebergIOManager` to read and write iceberg tables using Pandas:

    ```python title="docs/snippets/io_manager_pandas.py" linenums="1"
    --8<-- "docs/snippets/io_manager_pandas.py"
    ```

=== "Polars DataFrames"

     You can use the `PolarsIcebergIOManager` to read and write iceberg tables using Polars using a full lazily optimized query engine:

    ```python title="docs/snippets/io_manager_polars.py" linenums="1"
    --8<-- "docs/snippets/io_manager_polars.py"
    ```

=== "Daft DataFrames"

     You can use the `DaftIcebergIOManager` to read and write iceberg tables using Daft using a full lazily optimized query engine:

    ```python title="docs/snippets/io_manager_daft.py" linenums="1"
    --8<-- "docs/snippets/io_manager_daft.py"
    ```

---

## Executing custom SQL commands with the Iceberg resource

In addition to the Iceberg I/O manager, Dagster also provides a Iceberg resource for executing custom SQL queries.

```python title="docs/snippets/Iceberg_resource.py" linenums="1"
--8<-- "docs/snippets/Iceberg_resource.py"
```

In this example, we attach the Iceberg resource to the small_petals asset. In the body of the asset function, we use the `load()` method to retrieve the Iceberg `Table` object, which can then be used for further processing.

For more information on the Iceberg resource, see the Iceberg resource API docs.

---

## Configuring table behavior using table properties

Iceberg tables support table properties to configure table behavior. You can see a full list of properties [here](https://py.iceberg.apache.org/configuration/).

Use asset metadata to set table properties:

```python title="docs/snippets/table_properties.py" linenums="1"
--8<-- "docs/snippets/table_properties.py"
```

---

## Using upsert mode to update and insert data

The Iceberg I/O manager supports upsert operations, which allow you to update existing rows and insert new rows in a single operation. This is useful for maintaining slowly changing dimensions or incrementally updating tables.

### Upsert options
Upsert options can be set at deployment time via asset definition metadata, or dynamically at runtime via output metadata. Upsert options set at runtime via `context.add_output_metadata()` take precedence over those set in definition metadata.

**Required**:
  - **join_cols**: list[str] - list of columns that make up the join key for the upsert operation

**Optional**:
  - **when_matched_update_all**: bool - Whether to update rows in the target table that join with the dataframe being upserted (default True)
  - **when_not_matched_insert_all**: bool - Whether to insert all rows from the upsert dataframe that do not join with the target table (default True)


To use upsert mode, set the `write_mode` to `"upsert"` and provide `upsert_options` in the asset or output metadata:

```python
import pyarrow as pa
from dagster import asset, AssetExecutionContext

@asset(
    metadata={
        "write_mode": "upsert",
        "upsert_options": {
            "join_cols": ["id"],  # Columns to join on for matching
            "when_matched_update_all": True,  # Update all columns when matched
            "when_not_matched_insert_all": True,  # Insert all columns when not matched
        }
    }
)
def user_profiles(context: AssetExecutionContext) -> pa.Table:
    # Returns a table with user profiles
    # Rows with matching 'id' will be updated
    # Rows with new 'id' values will be inserted
    return pa.table({
        "id": [1, 2, 3],
        "name": ["Alice", "Bob", "Charlie"],
        "updated_at": ["2024-01-01", "2024-01-02", "2024-01-03"]
    })
```

You can also override upsert options at runtime using output metadata:

```python
@asset(
    metadata={
        "write_mode": "upsert",
        "upsert_options": {
            "join_cols": ["id"],
            "when_matched_update_all": True,
            "when_not_matched_insert_all": True,
        }
    }
)
def user_profiles_dynamic(context: AssetExecutionContext) -> pa.Table:
    # Override upsert options at runtime based on business logic
    if context.run.tags.get("update_mode") == "id_and_timestamp":
        context.add_output_metadata({
            "upsert_options": {
                "join_cols": ["id", "timestamp"],  # Join on multiple columns
                "when_matched_update_all": False,
                "when_not_matched_insert_all": False,
            }
        })

    return pa.table({
        "id": [1, 2, 3],
        "timestamp": ["2024-01-01", "2024-01-01", "2024-01-01"],
        "name": ["Alice", "Bob", "Charlie"],
    })
```

You can use the `UpsertOptions` `BaseModel` subclass to represent upsert options metadata to provide deployment-time type validation:

```python
from dagster_iceberg.config import UpsertOptions

@asset(
    metadata={
        "write_mode": "upsert",
        "upsert_options": UpsertOptions(
            join_cols=["id", "timestamp"],
            when_matched_update_all=True,
            when_not_matched_insert_all=True,
        )
    }
)
def my_table_typed_upsert(context: AssetExecutionContext, my_table: pa.Table):
    context.add_output_metadata({"upsert_options": UpsertOptions(
                join_cols=["id", "timestamp"],
                when_matched_update_all=True,
                when_not_matched_insert_all=False,
            )
        }
    )
```

---

## Allowing updates to schema and partitions

By default, assets will error when you change the partition spec (e.g. if you change a partition from hourly to daily) or the schema (e.g. when you add a column). You can allow updates to an asset's partition spec and/or schema by adding the following configuration options to the asset metadata:

```python
@asset(
    partitions_def=MultiPartitionsDefinition(
        {
            "date": DailyPartitionsDefinition(start_date="2023-01-01"),
            "species": StaticPartitionDefinition(
                ["Iris-setosa", "Iris-virginica", "Iris-versicolor"]
            ),
        }
    ),
    metadata={
        "partition_expr": {"date": "time", "species": "species"},
        "partition_spec_update_mode": "update",
        "schema_update_mode": "update"
    },
)
def iris_dataset_partitioned(context) -> pd.DataFrame:
    ...
```

---

## Using the custom DB IO Manager

The `dagster-iceberg` library leans heavily on Dagster's `DbIOManager` implementation. This IO manager comes with some limitations, however, such as the lack of support for various [partition mappings](https://docs.dagster.io/_apidocs/partitions#partition-mapping). A custom (experimental) `DbIOManager` implementation is available that supports partition mappings as long as any time-based partition is *consecutive* and static partitions are of string type. You can enable it as follows:

```python
from dagster_iceberg.config import IcebergCatalogConfig
from dagster_iceberg.io_manager.arrow import PyArrowIcebergIOManager


PyArrowIcebergIOManager(
    name="my_catalog",
    config=IcebergCatalogConfig(properties={...}),
    namespace="my_schema",
    db_io_manager="custom"
)
```

For example, a `MultiToSingleDimensionPartitionMapping` is supported:

```python
@asset(
    key_prefix=["my_schema"],
    partitions_def=daily_partitions_def,
    ins={
        "multi_partitioned_asset": AssetIn(
            ["my_schema", "multi_partitioned_asset_1"],
            partition_mapping=MultiToSingleDimensionPartitionMapping(
                partition_dimension_name="date"
            ),
        )
    },
    metadata={
        "partition_expr": "date_column",
    },
)
def single_partitioned_asset_date(multi_partitioned_asset: pa.Table) -> pa.Table:
    ...
```

But a `SpecificPartitionsPartitionMapping` is not because these dates are not consecutive:

```python
@asset(
    partitions_def=multi_partition_with_letter,
    key_prefix=["my_schema"],
    metadata={"partition_expr": {"time": "time", "letter": "letter"}},
    ins={
        "multi_partitioned_asset": AssetIn(
            ["my_schema", "multi_partitioned_asset_1"],
            partition_mapping=MultiPartitionMapping(
                {
                    "color": DimensionPartitionMapping(
                        dimension_name="letter",
                        partition_mapping=StaticPartitionMapping(
                            {"blue": "a", "red": "b", "yellow": "c"}
                        ),
                    ),
                    "date": DimensionPartitionMapping(
                        dimension_name="date",
                        partition_mapping=SpecificPartitionsPartitionMapping(
                            ["2022-01-01", "2024-01-01"]
                        ),
                    ),
                }
            ),
        )
    },
)
def mapped_multi_partition(
    context: AssetExecutionContext, multi_partitioned_asset: pa.Table
) -> pa.Table:
    ...
```
