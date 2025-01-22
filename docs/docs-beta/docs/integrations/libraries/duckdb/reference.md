---
title: "dagster-duckdb integration reference"
description: Store your Dagster assets in DuckDB
sidebar_position: 200
---

This reference page provides information for working with [`dagster-duckdb`](/api/python-api/libraries/dagster-duckdb) features that are not covered as part of the [Using Dagster with DuckDB tutorial](using-duckdb-with-dagster).

DuckDB resource:

- [Executing custom SQL queries](#executing-custom-sql-queries)

DuckDB I/O manager:

- [Selecting specific columns in a downstream asset](#selecting-specific-columns-in-a-downstream-asset)
- [Storing partitioned assets](#storing-partitioned-assets)
- [Storing tables in multiple schemas](#storing-tables-in-multiple-schemas)
- [Using the DuckDB I/O manager with other I/O managers](#using-the-duckdb-io-manager-with-other-io-managers)
- [Storing and loading PySpark or Polars DataFrames in DuckDB](#storing-and-loading-pyspark-or-polars-dataframes-in-duckdb)
- [Storing multiple DataFrame types in DuckDB](#storing-multiple-dataframe-types-in-duckdb)

## DuckDB resource

The DuckDB resource provides access to a [`duckdb.DuckDBPyConnection`](https://duckdb.org/docs/api/python/reference/#duckdb.DuckDBPyConnection) object. This allows you full control over how your data is stored and retrieved in your database.

For further information on the DuckDB resource, see the [DuckDB resource API docs](/api/python-api/libraries/dagster-duckdb#dagster_duckdb.DuckDBResource).

### Executing custom SQL queries

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/resource.py startafter=start endbefore=end
from dagster_duckdb import DuckDBResource

from dagster import asset

# this example executes a query against the iris_dataset table created in Step 2 of the
# Using Dagster with DuckDB tutorial


@asset(deps=[iris_dataset])
def small_petals(duckdb: DuckDBResource) -> None:
    with duckdb.get_connection() as conn:  # conn is a DuckDBPyConnection
        conn.execute(
            "CREATE TABLE iris.small_petals AS SELECT * FROM iris.iris_dataset WHERE"
            " 'petal_length_cm' < 1 AND 'petal_width_cm' < 1"
        )
```

In this example, we attach the DuckDB resource to the `small_petals` asset. In the body of the asset function, we use the `get_connection` context manager on the resource to get a [`duckdb.DuckDBPyConnection`](https://duckdb.org/docs/api/python/reference/#duckdb.DuckDBPyConnection). We can use this connection to execute a custom SQL query against the `iris_dataset` table created in [Step 2: Create tables in DuckDB](using-duckdb-with-dagster#option-1-step-2) of the [Using Dagster with DuckDB tutorial](using-duckdb-with-dagster). When the `duckdb.get_connection` context is exited, the DuckDB connection will be closed.

## DuckDB I/O manager

The DuckDB I/O manager provides several ways to customize how your data is stored and loaded in DuckDB. However, if you find that these options do not provide enough customization for your use case, we recommend using the DuckDB resource to save and load your data. By using the resource, you will have more fine-grained control over how your data is handled, since you have full control over the SQL queries that are executed.

### Selecting specific columns in a downstream asset

Sometimes you may not want to fetch an entire table as the input to a downstream asset. With the DuckDB I/O manager, you can select specific columns to load by supplying metadata on the downstream asset.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/downstream_columns.py
import pandas as pd

from dagster import AssetIn, asset

# this example uses the iris_dataset asset from Step 2 of the Using Dagster with DuckDB tutorial


@asset(
    ins={
        "iris_sepal": AssetIn(
            key="iris_dataset",
            metadata={"columns": ["sepal_length_cm", "sepal_width_cm"]},
        )
    }
)
def sepal_data(iris_sepal: pd.DataFrame) -> pd.DataFrame:
    iris_sepal["sepal_area_cm2"] = (
        iris_sepal["sepal_length_cm"] * iris_sepal["sepal_width_cm"]
    )
    return iris_sepal
```

In this example, we only use the columns containing sepal data from the `IRIS_DATASET` table created in [Step 2: Create tables in DuckDB](using-duckdb-with-dagster#option-2-step-2) of the [Using Dagster with DuckDB tutorial](using-duckdb-with-dagster). To select specific columns, we can add metadata to the input asset. We do this in the `metadata` parameter of the `AssetIn` that loads the `iris_dataset` asset in the `ins` parameter. We supply the key `columns` with a list of names of the columns we want to fetch.

When Dagster materializes `sepal_data` and loads the `iris_dataset` asset using the DuckDB I/O manager, it will only fetch the `sepal_length_cm` and `sepal_width_cm` columns of the `IRIS.IRIS_DATASET` table and pass them to `sepal_data` as a Pandas DataFrame.

### Storing partitioned assets

The DuckDB I/O manager supports storing and loading partitioned data. To correctly store and load data from the DuckDB table, the DuckDB I/O manager needs to know which column contains the data defining the partition bounds. The DuckDB I/O manager uses this information to construct the correct queries to select or replace the data.

In the following sections, we describe how the I/O manager constructs these queries for different types of partitions.

<Tabs>
<TabItem value="Static partitioned assets" label="Storing static partitioned assets">

To store static partitioned assets in DuckDB, specify `partition_expr` metadata on the asset to tell the DuckDB I/O manager which column contains the partition data:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/static_partition.py startafter=start_example endbefore=end_example
import pandas as pd

from dagster import AssetExecutionContext, StaticPartitionsDefinition, asset


@asset(
    partitions_def=StaticPartitionsDefinition(
        ["Iris-setosa", "Iris-virginica", "Iris-versicolor"]
    ),
    metadata={"partition_expr": "SPECIES"},
)
def iris_dataset_partitioned(context: AssetExecutionContext) -> pd.DataFrame:
    species = context.partition_key

    full_df = pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )

    return full_df[full_df["Species"] == species]


@asset
def iris_cleaned(iris_dataset_partitioned: pd.DataFrame):
    return iris_dataset_partitioned.dropna().drop_duplicates()
```

Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the partition in the downstream asset. When loading a static partition (or multiple static partitions), the following statement is used:

```sql
SELECT *
 WHERE [partition_expr] in ([selected partitions])
```

When the `partition_expr` value is injected into this statement, the resulting SQL query must follow DuckDB's SQL syntax. Refer to the [DuckDB documentation](https://duckdb.org/docs/sql/query_syntax/select) for more information.

{/* TODO fix link A partition must be selected when materializing the above assets, as described in the [Materializing partitioned assets](/concepts/partitions-schedules-sensors/partitioning-assets#materializing-partitioned-assets) documentation. */} A partition must be selected when materializing the above assets. In this example, the query used when materializing the `Iris-setosa` partition of the above assets would be:

```sql
SELECT *
 WHERE SPECIES in ('Iris-setosa')
```

</TabItem>
<TabItem value="Time partitioned assets" label="Storing time-partitioned assets">

Like static partitioned assets, you can specify `partition_expr` metadata on the asset to tell the DuckDB I/O manager which column contains the partition data:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/time_partition.py startafter=start_example endbefore=end_example
import pandas as pd

from dagster import AssetExecutionContext, DailyPartitionsDefinition, asset


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
    metadata={"partition_expr": "TO_TIMESTAMP(TIME)"},
)
def iris_data_per_day(context: AssetExecutionContext) -> pd.DataFrame:
    partition = context.partition_key

    # get_iris_data_for_date fetches all of the iris data for a given date,
    # the returned dataframe contains a column named 'time' with that stores
    # the time of the row as an integer of seconds since epoch
    return get_iris_data_for_date(partition)


@asset
def iris_cleaned(iris_data_per_day: pd.DataFrame):
    return iris_data_per_day.dropna().drop_duplicates()
```

Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the correct partition in the downstream asset. When loading a dynamic partition, the following statement is used:

```sql
SELECT *
 WHERE [partition_expr] >= [partition_start]
   AND [partition_expr] < [partition_end]
```

When the `partition_expr` value is injected into this statement, the resulting SQL query must follow DuckDB's SQL syntax. Refer to the [DuckDB documentation](https://duckdb.org/docs/sql/query_syntax/select) for more information.

{/* TODO fix link: A partition must be selected when materializing the above assets, as described in the [Materializing partitioned assets](/concepts/partitions-schedules-sensors/partitioning-assets#materializing-partitioned-assets) documentation. */} A partition must be selected when materializing assets. The `[partition_start]` and `[partition_end]` bounds are of the form `YYYY-MM-DD HH:MM:SS`. In this example, the query when materializing the `2023-01-02` partition of the above assets would be:

```sql
SELECT *
 WHERE TO_TIMESTAMP(TIME) >= '2023-01-02 00:00:00'
   AND TO_TIMESTAMP(TIME) < '2023-01-03 00:00:00'
```

In this example, the data in the `TIME` column are integers, so the `partition_expr` metadata includes a SQL statement to convert integers to timestamps. A full list of DuckDB functions can be found [here](https://duckdb.org/docs/sql/functions/overview).

</TabItem>
<TabItem value="Multi-partitioned assets" label="Storing multi-partitioned assets">

The DuckDB I/O manager can also store data partitioned on multiple dimensions. To do this, specify the column for each partition as a dictionary of `partition_expr` metadata:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/multi_partition.py startafter=start_example endbefore=end_example
import pandas as pd

from dagster import (
    AssetExecutionContext,
    DailyPartitionsDefinition,
    MultiPartitionsDefinition,
    StaticPartitionsDefinition,
    asset,
)


@asset(
    partitions_def=MultiPartitionsDefinition(
        {
            "date": DailyPartitionsDefinition(start_date="2023-01-01"),
            "species": StaticPartitionsDefinition(
                ["Iris-setosa", "Iris-virginica", "Iris-versicolor"]
            ),
        }
    ),
    metadata={"partition_expr": {"date": "TO_TIMESTAMP(TIME)", "species": "SPECIES"}},
)
def iris_dataset_partitioned(context: AssetExecutionContext) -> pd.DataFrame:
    partition = context.partition_key.keys_by_dimension
    species = partition["species"]
    date = partition["date"]

    # get_iris_data_for_date fetches all of the iris data for a given date,
    # the returned dataframe contains a column named 'time' with that stores
    # the time of the row as an integer of seconds since epoch
    full_df = get_iris_data_for_date(date)

    return full_df[full_df["species"] == species]


@asset
def iris_cleaned(iris_dataset_partitioned: pd.DataFrame):
    return iris_dataset_partitioned.dropna().drop_duplicates()
```

Dagster uses the `partition_expr` metadata to craft the `SELECT` statement when loading the correct partition in a downstream asset. For multi-partitions, Dagster concatenates the `WHERE` statements described in the above sections to craft the correct `SELECT` statement.

{/* TODO fix link: A partition must be selected when materializing the above assets, as described in the [Materializing partitioned assets](/concepts/partitions-schedules-sensors/partitioning-assets#materializing-partitioned-assets) documentation. */} A partition must be selected when materializing assets. For example, when materializing the `2023-01-02|Iris-setosa` partition of the above assets, the following query will be used:

```sql
SELECT *
 WHERE SPECIES in ('Iris-setosa')
   AND TO_TIMESTAMP(TIME) >= '2023-01-02 00:00:00'
   AND TO_TIMESTAMP(TIME) < '2023-01-03 00:00:00'
```

In this example, the data in the `TIME` column are integers, so the `partition_expr` metadata includes a SQL statement to convert integers to timestamps. A full list of DuckDB functions can be found [here](https://duckdb.org/docs/sql/functions/overview).

</TabItem>
</Tabs>

### Storing tables in multiple schemas

You may want to have different assets stored in different DuckDB schemas. The DuckDB I/O manager allows you to specify the schema in several ways.

You can specify the default schema where data will be stored as configuration to the I/O manager, as we did in [Step 1: Configure the DuckDB I/O manager](using-duckdb-with-dagster#step-1-configure-the-duckdb-io-manager) of the [Using Dagster with DuckDB tutorial](using-duckdb-with-dagster).

If you want to store assets in different schemas, you can specify the schema as metadata:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/schema.py startafter=start_metadata endbefore=end_metadata dedent=4
daffodil_dataset = AssetSpec(
    key=["daffodil_dataset"], metadata={"schema": "daffodil"}
)

@asset(metadata={"schema": "iris"})
def iris_dataset() -> pd.DataFrame:
    return pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )
```

You can also specify the schema as part of the asset's key:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/schema.py startafter=start_asset_key endbefore=end_asset_key dedent=4
daffodil_dataset = AssetSpec(key=["daffodil", "daffodil_dataset"])

@asset(key_prefix=["iris"])
def iris_dataset() -> pd.DataFrame:
    return pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )
```

In this example, the `iris_dataset` asset will be stored in the `IRIS` schema, and the `daffodil_dataset` asset will be found in the `DAFFODIL` schema.

:::

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

### Using the DuckDB I/O manager with other I/O managers

You may have assets that you don't want to store in DuckDB. You can provide an I/O manager to each asset using the `io_manager_key` parameter in the <PyObject section="assets" module="dagster" object="asset" decorator /> decorator:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/multiple_io_managers.py startafter=start_example endbefore=end_example
import pandas as pd
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_duckdb_pandas import DuckDBPandasIOManager

from dagster import Definitions, asset


@asset(io_manager_key="warehouse_io_manager")
def iris_dataset() -> pd.DataFrame:
    return pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "sepal_width_cm",
            "petal_length_cm",
            "petal_width_cm",
            "species",
        ],
    )


@asset(io_manager_key="blob_io_manager")
def iris_plots(iris_dataset):
    # plot_data is a function we've defined somewhere else
    # that plots the data in a DataFrame
    return plot_data(iris_dataset)


defs = Definitions(
    assets=[iris_dataset, iris_plots],
    resources={
        "warehouse_io_manager": DuckDBPandasIOManager(
            database="path/to/my_duckdb_database.duckdb",
            schema="IRIS",
        ),
        "blob_io_manager": s3_pickle_io_manager,
    },
)
```

In this example:

- The `iris_dataset` asset uses the I/O manager bound to the key `warehouse_io_manager` and `iris_plots` uses the I/O manager bound to the key `blob_io_manager`
- In the <PyObject section="definitions" module="dagster" object="Definitions" /> object, we supply the I/O managers for those keys
- When the assets are materialized, the `iris_dataset` will be stored in DuckDB, and `iris_plots` will be saved in Amazon S3

### Storing and loading PySpark or Polars DataFrames in DuckDB

The DuckDB I/O manager also supports storing and loading PySpark and Polars DataFrames.

<Tabs>
<TabItem value="PySpark DataFrames" label="Storing and loading PySpark DataFrames in DuckDB">

To use the <PyObject section="libraries" module="dagster_duckdb_pyspark" object="DuckDBPySparkIOManager" />, first install the package:

```shell
pip install dagster-duckdb-pyspark
```

Then you can use the `DuckDBPySparkIOManager` in your <PyObject section="definitions" module="dagster" object="Definitions" /> as in [Step 1: Configure the DuckDB I/O manager](using-duckdb-with-dagster#step-1-configure-the-duckdb-io-manager) of the [Using Dagster with DuckDB tutorial](using-duckdb-with-dagster).

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/pyspark_configuration.py startafter=start_configuration endbefore=end_configuration
from dagster_duckdb_pyspark import DuckDBPySparkIOManager

from dagster import Definitions

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": DuckDBPySparkIOManager(
            database="path/to/my_duckdb_database.duckdb",  # required
            schema="IRIS",  # optional, defaults to PUBLIC
        )
    },
)
```

The `DuckDBPySparkIOManager` requires an active `SparkSession`. You can either create your own `SparkSession` or use the <PyObject section="libraries" module="dagster_spark" object="spark_resource"/>.

<Tabs>
<TabItem value="With the spark_resource">

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/pyspark_with_spark_resource.py
from dagster_duckdb_pyspark import DuckDBPySparkIOManager
from dagster_pyspark import pyspark_resource
from pyspark import SparkFiles
from pyspark.sql import DataFrame
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

from dagster import AssetExecutionContext, Definitions, asset


@asset(required_resource_keys={"pyspark"})
def iris_dataset(context: AssetExecutionContext) -> DataFrame:
    spark = context.resources.pyspark.spark_session

    schema = StructType(
        [
            StructField("sepal_length_cm", DoubleType()),
            StructField("sepal_width_cm", DoubleType()),
            StructField("petal_length_cm", DoubleType()),
            StructField("petal_width_cm", DoubleType()),
            StructField("species", StringType()),
        ]
    )

    url = "https://docs.dagster.io/assets/iris.csv"
    spark.sparkContext.addFile(url)

    return spark.read.schema(schema).csv("file://" + SparkFiles.get("iris.csv"))


defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": DuckDBPySparkIOManager(
            database="path/to/my_duckdb_database.duckdb",
            schema="IRIS",
        ),
        "pyspark": pyspark_resource,
    },
)
```

</TabItem>
<TabItem value="With your own SparkSession">

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/pyspark_with_spark_session.py startafter=start endbefore=end
from dagster_duckdb_pyspark import DuckDBPySparkIOManager
from pyspark import SparkFiles
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

from dagster import Definitions, asset


@asset
def iris_dataset() -> DataFrame:
    spark = SparkSession.builder.getOrCreate()

    schema = StructType(
        [
            StructField("sepal_length_cm", DoubleType()),
            StructField("sepal_width_cm", DoubleType()),
            StructField("petal_length_cm", DoubleType()),
            StructField("petal_width_cm", DoubleType()),
            StructField("species", StringType()),
        ]
    )

    url = "https://docs.dagster.io/assets/iris.csv"
    spark.sparkContext.addFile(url)

    return spark.read.schema(schema).csv("file://" + SparkFiles.get("iris.csv"))


defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": DuckDBPySparkIOManager(
            database="path/to/my_duckdb_database.duckdb",
            schema="IRIS",
        )
    },
)
```

</TabItem>
</Tabs>

</TabItem>
<TabItem value="Polars DataFrames" label="Storing and loading Polars DataFrames in DuckDB">

To use the <PyObject section="libraries" module="dagster_duckdb_polars" object="DuckDBPolarsIOManager" />, first install the package:

```shell
pip install dagster-duckdb-polars
```

Then you can use the `DuckDBPolarsIOManager` in your <PyObject section="definitions" module="dagster" object="Definitions" /> as in [Step 1: Configure the DuckDB I/O manager](using-duckdb-with-dagster#step-1-configure-the-duckdb-io-manager) of the [Using Dagster with DuckDB tutorial](using-duckdb-with-dagster).

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/polars_configuration.py startafter=start_configuration endbefore=end_configuration
from dagster_duckdb_polars import DuckDBPolarsIOManager

from dagster import Definitions

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": DuckDBPolarsIOManager(
            database="path/to/my_duckdb_database.duckdb",  # required
            schema="IRIS",  # optional, defaults to PUBLIC
        )
    },
)
```

</TabItem>
</Tabs>

### Storing multiple DataFrame types in DuckDB

If you work with several DataFrame libraries and want a single I/O manager to handle storing and loading these DataFrames in DuckDB, you can write a new I/O manager that handles the DataFrame types.

To do this, inherit from the <PyObject section="libraries" module="dagster_duckdb" object="DuckDBIOManager" /> base class and implement the `type_handlers` and `default_load_type` methods. The resulting I/O manager will inherit the configuration fields of the base `DuckDBIOManager`.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/duckdb/reference/multiple_dataframe_types.py startafter=start_example endbefore=end_example
from typing import Optional, Type

import pandas as pd
from dagster_duckdb import DuckDBIOManager
from dagster_duckdb_pandas import DuckDBPandasTypeHandler
from dagster_duckdb_polars import DuckDBPolarsTypeHandler
from dagster_duckdb_pyspark import DuckDBPySparkTypeHandler

from dagster import Definitions


class DuckDBPandasPySparkPolarsIOManager(DuckDBIOManager):
    @staticmethod
    def type_handlers():
        """type_handlers should return a list of the TypeHandlers that the I/O manager can use.
        Here we return the DuckDBPandasTypeHandler, DuckDBPySparkTypeHandler, and DuckDBPolarsTypeHandler so that the I/O
        manager can store Pandas DataFrames, PySpark DataFrames, and Polars DataFrames.
        """
        return [
            DuckDBPandasTypeHandler(),
            DuckDBPySparkTypeHandler(),
            DuckDBPolarsTypeHandler(),
        ]

    @staticmethod
    def default_load_type() -> Optional[type]:
        """If an asset is not annotated with an return type, default_load_type will be used to
        determine which TypeHandler to use to store and load the output.
        In this case, unannotated assets will be stored and loaded as Pandas DataFrames.
        """
        return pd.DataFrame


defs = Definitions(
    assets=[iris_dataset, rose_dataset],
    resources={
        "io_manager": DuckDBPandasPySparkPolarsIOManager(
            database="path/to/my_duckdb_database.duckdb",
            schema="IRIS",
        )
    },
)
```
