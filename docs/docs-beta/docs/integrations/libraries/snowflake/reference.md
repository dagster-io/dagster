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

{/* TODO convert to <CodeExample> */}
```python file=/integrations/snowflake/private_key_auth_resource.py startafter=start_direct_key endbefore=end_direct_key
from dagster_snowflake import SnowflakeResource

from dagster import Definitions, EnvVar

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "snowflake": SnowflakeResource(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            private_key=EnvVar("SNOWFLAKE_PK"),
            private_key_password=EnvVar("SNOWFLAKE_PK_PASSWORD"),
            database="FLOWERS",
        )
    },
)
```

**Via a file**

{/* TODO convert to <CodeExample> */}
```python file=/integrations/snowflake/private_key_auth_resource.py startafter=start_key_file endbefore=end_key_file
from dagster_snowflake import SnowflakeResource

from dagster import Definitions, EnvVar

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "snowflake": SnowflakeResource(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            private_key_path="/path/to/private/key/file.p8",
            private_key_password=EnvVar("SNOWFLAKE_PK_PASSWORD"),
            database="FLOWERS",
        )
    },
)
```

</TabItem>
<TabItem value="I/O managers" label="I/O managers">

**Directly to the I/O manager**

{/* TODO convert to <CodeExample> */}
```python file=/integrations/snowflake/private_key_auth_io_manager.py startafter=start_direct_key endbefore=end_direct_key
from dagster_snowflake_pandas import SnowflakePandasIOManager

from dagster import Definitions, EnvVar

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": SnowflakePandasIOManager(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            private_key=EnvVar("SNOWFLAKE_PK"),
            private_key_password=EnvVar("SNOWFLAKE_PK_PASSWORD"),
            database="FLOWERS",
        )
    },
)
```

**Via a file**

{/* TODO convert to <CodeExample> */}
```python file=/integrations/snowflake/private_key_auth_io_manager.py startafter=start_key_file endbefore=end_key_file
from dagster_snowflake_pandas import SnowflakePandasIOManager

from dagster import Definitions, EnvVar

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": SnowflakePandasIOManager(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            private_key_path="/path/to/private/key/file.p8",
            private_key_password=EnvVar("SNOWFLAKE_PK_PASSWORD"),
            database="FLOWERS",
        )
    },
)
```

</TabItem>
</Tabs>

## Using the Snowflake resource

### Executing custom SQL commands

Using a [Snowflake resource](/api/python-api/libraries/dagster-snowflake#resource), you can execute custom SQL queries on a Snowflake database:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/snowflake/resource.py startafter=start endbefore=end
from dagster_snowflake import SnowflakeResource

from dagster import Definitions, EnvVar, asset

# this example executes a query against the IRIS_DATASET table created in Step 2 of the
# Using Dagster with Snowflake tutorial


@asset
def small_petals(snowflake: SnowflakeResource):
    query = """
        create or replace table iris.small_petals as (
            SELECT *
            FROM iris.iris_dataset
            WHERE species = 'petal_length_cm' < 1 AND 'petal_width_cm' < 1
        );
    """

    with snowflake.get_connection() as conn:
        conn.cursor.execute(query)


defs = Definitions(
    assets=[small_petals],
    resources={
        "snowflake": SnowflakeResource(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database="FLOWERS",
            schema="IRIS",
        )
    },
)
```

Let's review what's happening in this example:

- Attached the `SnowflakeResource` to the `small_petals` asset
- Used the `get_connection` context manager method of the Snowflake resource to get a [`snowflake.connector.Connection`](https://docs.snowflake.com/en/developer-guide/python-connector/python-connector-api#object-connection) object
- Used the connection to execute a custom SQL query against the `IRIS_DATASET` table created in [Step 2](using-snowflake-with-dagster#step-2-create-tables-in-snowflake) of the [Snowflake resource tutorial](using-snowflake-with-dagster)

For more information on the Snowflake resource, including additional configuration settings, see the <PyObject section="libraries" object="SnowflakeResource" module="dagster_snowflake" /> API docs.


## Using the Snowflake I/O manager

### Selecting specific columns in a downstream asset

Sometimes you may not want to fetch an entire table as the input to a downstream asset. With the Snowflake I/O manager, you can select specific columns to load by supplying metadata on the downstream asset.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/snowflake/downstream_columns.py
import pandas as pd

from dagster import AssetIn, asset

# this example uses the iris_dataset asset from Step 2 of the Using Dagster with Snowflake tutorial


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

In this example, we only use the columns containing sepal data from the `IRIS_DATASET` table created in [Step 2](using-snowflake-with-dagster-io-managers#store-a-dagster-asset-as-a-table-in-snowflake) of the [Snowflake I/O manager tutorial](using-snowflake-with-dagster-io-managers). Fetching the entire table would be unnecessarily costly, so to select specific columns, we can add metadata to the input asset. We do this in the `metadata` parameter of the `AssetIn` that loads the `iris_dataset` asset in the `ins` parameter. We supply the key `columns` with a list of names of the columns we want to fetch.

When Dagster materializes `sepal_data` and loads the `iris_dataset` asset using the Snowflake I/O manager, it will only fetch the `sepal_length_cm` and `sepal_width_cm` columns of the `FLOWERS.IRIS.IRIS_DATASET` table and pass them to `sepal_data` as a Pandas DataFrame.

### Storing partitioned assets

The Snowflake I/O manager supports storing and loading partitioned data. In order to correctly store and load data from the Snowflake table, the Snowflake I/O manager needs to know which column contains the data defining the partition bounds. The Snowflake I/O manager uses this information to construct the correct queries to select or replace the data. In the following sections, we describe how the I/O manager constructs these queries for different types of partitions.

<Tabs>
<TabItem value="Statically-partitioned assets" label="Statically-partitioned assets">

To store statically-partitioned assets in Snowflake, specify `partition_expr` metadata on the asset to tell the Snowflake I/O manager which column contains the partition data:

{/* TODO convert to CodeExample */}
```python file=/integrations/snowflake/static_partition.py
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

When the `partition_expr` value is injected into this statement, the resulting SQL query must follow Snowflake's SQL syntax. Refer to the [Snowflake documentation](https://docs.snowflake.com/en/sql-reference/constructs) for more information.

{/* TODO fix link: When materializing the above assets, a partition must be selected, as described in [Materializing partitioned assets](/concepts/partitions-schedules-sensors/partitioning-assets#materializing-partitioned-assets).*/} When materializing the above assets, a partition must be selected. In this example, the query used when materializing the `Iris-setosa` partition of the above assets would be:

```sql
SELECT *
 WHERE SPECIES in ('Iris-setosa')
```

</TabItem>
<TabItem value="Time-partitioned assets">

Like statically-partitioned assets, you can specify `partition_expr` metadata on the asset to tell the Snowflake I/O manager which column contains the partition data:

{/* TODO convert to CodeExample */}
```python file=/integrations/snowflake/time_partition.py startafter=start_example endbefore=end_example
import pandas as pd

from dagster import AssetExecutionContext, DailyPartitionsDefinition, asset


@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2023-01-01"),
    metadata={"partition_expr": "TO_TIMESTAMP(TIME::INT)"},
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

{/* TODO convert to CodeExample */}
```python file=/integrations/snowflake/multi_partition.py startafter=start_example endbefore=end_example
import pandas as pd

from dagster import (
    AssetExecutionContext,
    DailyPartitionsDefinition,
    MultiPartitionKey,
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
    metadata={
        "partition_expr": {"date": "TO_TIMESTAMP(TIME::INT)", "species": "SPECIES"}
    },
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

{/* TODO convert to <CodeExample> */}
```python file=/integrations/snowflake/schema.py startafter=start_metadata endbefore=end_metadata dedent=4
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

You can also specify the schema as part of the asset's asset key:

{/* TODO convert to <CodeExample> */}
```python file=/integrations/snowflake/schema.py startafter=start_asset_key endbefore=end_asset_key dedent=4
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

{/* TODO convert to <CodeExample> */}
```python file=/integrations/snowflake/multiple_io_managers.py startafter=start_example endbefore=end_example
import pandas as pd
from dagster_aws.s3.io_manager import s3_pickle_io_manager
from dagster_snowflake_pandas import SnowflakePandasIOManager

from dagster import Definitions, EnvVar, asset


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
        "warehouse_io_manager": SnowflakePandasIOManager(
            database="FLOWERS",
            schema="IRIS",
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
        ),
        "blob_io_manager": s3_pickle_io_manager,
    },
)
```

In this example, the `iris_dataset` asset uses the I/O manager bound to the key `warehouse_io_manager` and `iris_plots` will use the I/O manager bound to the key `blob_io_manager`. In the <PyObject section="definitions" module="dagster" object="Definitions" /> object, we supply the I/O managers for those keys. When the assets are materialized, the `iris_dataset` will be stored in Snowflake, and `iris_plots` will be saved in Amazon S3.

### Storing and loading PySpark DataFrames in Snowflake

The Snowflake I/O manager also supports storing and loading PySpark DataFrames. To use the <PyObject section="libraries" module="dagster_snowflake_pyspark" object="SnowflakePySparkIOManager" />, first install the package:

```shell
pip install dagster-snowflake-pyspark
```

Then you can use the `SnowflakePySparkIOManager` in your `Definitions` as in [Step 1](using-snowflake-with-dagster-io-managers#step-1-configure-the-snowflake-io-manager) of the [Snowflake I/O manager tutorial](using-snowflake-with-dagster-io-managers).

{/* TODO convert to <CodeExample> */}
```python file=/integrations/snowflake/pyspark_configuration.py startafter=start_configuration endbefore=end_configuration
from dagster_snowflake_pyspark import SnowflakePySparkIOManager

from dagster import Definitions, EnvVar

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": SnowflakePySparkIOManager(
            account="abc1234.us-east-1",  # required
            user=EnvVar("SNOWFLAKE_USER"),  # required
            password=EnvVar("SNOWFLAKE_PASSWORD"),  # password or private key required
            database="FLOWERS",  # required
            warehouse="PLANTS",  # required for PySpark
            role="writer",  # optional, defaults to the default role for the account
            schema="IRIS",  # optional, defaults to PUBLIC
        )
    },
)
```

:::note

When using the `snowflake_pyspark_io_manager` the `warehouse` configuration is required.

:::

The `SnowflakePySparkIOManager` requires that a `SparkSession` be active and configured with the [Snowflake connector for Spark](https://docs.snowflake.com/en/user-guide/spark-connector.html). You can either create your own `SparkSession` or use the <PyObject section="libraries" module="dagster_spark" object="spark_resource"/>.

<Tabs>
<TabItem value="With the spark_resource">

{/* TODO convert to CodeExample */}
```python file=/integrations/snowflake/pyspark_with_spark_resource.py
from dagster_pyspark import pyspark_resource
from dagster_snowflake_pyspark import SnowflakePySparkIOManager
from pyspark import SparkFiles
from pyspark.sql import DataFrame
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

from dagster import AssetExecutionContext, Definitions, EnvVar, asset

SNOWFLAKE_JARS = "net.snowflake:snowflake-jdbc:3.8.0,net.snowflake:spark-snowflake_2.12:2.8.2-spark_3.0"


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
        "io_manager": SnowflakePySparkIOManager(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database="FLOWERS",
            warehouse="PLANTS",
            schema="IRIS",
        ),
        "pyspark": pyspark_resource.configured(
            {"spark_conf": {"spark.jars.packages": SNOWFLAKE_JARS}}
        ),
    },
)
```

</TabItem>
<TabItem value="With your own SparkSession">

{/* TODO convert to CodeExample */}
```python file=/integrations/snowflake/pyspark_with_spark_session.py
from dagster_snowflake_pyspark import SnowflakePySparkIOManager
from pyspark import SparkFiles
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import DoubleType, StringType, StructField, StructType

from dagster import Definitions, EnvVar, asset

SNOWFLAKE_JARS = "net.snowflake:snowflake-jdbc:3.8.0,net.snowflake:spark-snowflake_2.12:2.8.2-spark_3.0"


@asset
def iris_dataset() -> DataFrame:
    spark = SparkSession.builder.config(
        key="spark.jars.packages",
        value=SNOWFLAKE_JARS,
    ).getOrCreate()

    schema = StructType(
        [
            StructField("sepal_length_cm", DoubleType()),
            StructField("sepal_width_cm", DoubleType()),
            StructField("petal_length_cm", DoubleType()),
            StructField("petal_width_cm", DoubleType()),
            StructField("species", StringType()),
        ]
    )

    url = ("https://docs.dagster.io/assets/iris.csv",)
    spark.sparkContext.addFile(url)

    return spark.read.schema(schema).csv("file://" + SparkFiles.get("iris.csv"))


defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": SnowflakePySparkIOManager(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database="FLOWERS",
            warehouse="PLANTS",
            schema="IRIS",
        ),
    },
)
```

</TabItem>
</Tabs>

### Using Pandas and PySpark DataFrames with Snowflake

If you work with both Pandas and PySpark DataFrames and want a single I/O manager to handle storing and loading these DataFrames in Snowflake, you can write a new I/O manager that handles both types. To do this, inherit from the <PyObject section="libraries" module="dagster_snowflake" object="SnowflakeIOManager" /> base class and implement the `type_handlers` and `default_load_type` methods. The resulting I/O manager will inherit the configuration fields of the base `SnowflakeIOManager`.

{/* TODO convert to <CodeExample> */}
```python file=/integrations/snowflake/pandas_and_pyspark.py startafter=start_example endbefore=end_example
from typing import Optional, Type

import pandas as pd
from dagster_snowflake import SnowflakeIOManager
from dagster_snowflake_pandas import SnowflakePandasTypeHandler
from dagster_snowflake_pyspark import SnowflakePySparkTypeHandler

from dagster import Definitions, EnvVar


class SnowflakePandasPySparkIOManager(SnowflakeIOManager):
    @staticmethod
    def type_handlers():
        """type_handlers should return a list of the TypeHandlers that the I/O manager can use.
        Here we return the SnowflakePandasTypeHandler and SnowflakePySparkTypeHandler so that the I/O
        manager can store Pandas DataFrames and PySpark DataFrames.
        """
        return [SnowflakePandasTypeHandler(), SnowflakePySparkTypeHandler()]

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
        "io_manager": SnowflakePandasPySparkIOManager(
            account="abc1234.us-east-1",
            user=EnvVar("SNOWFLAKE_USER"),
            password=EnvVar("SNOWFLAKE_PASSWORD"),
            database="FLOWERS",
            role="writer",
            warehouse="PLANTS",
            schema="IRIS",
        )
    },
)
```
