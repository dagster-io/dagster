---
title: 'Storing assets in PostgreSQL with I/O managers'
sidebar_label: 'PostgreSQL I/O manager'
description: Let Dagster store Pandas DataFrames as PostgreSQL tables and load them back with the PostgreSQL I/O manager.
sidebar_position: 100
---

The `dagster-postgres-pandas` library provides an [I/O manager](/guides/build/io-managers) that stores Pandas DataFrames returned from assets and ops as PostgreSQL tables, and loads those tables back into DataFrames when they are used as inputs. It follows the same conventions as the DuckDB, Snowflake and BigQuery I/O managers, so assets written for one of those can be pointed at PostgreSQL without changes.

## Prerequisites

- **Install** the libraries:

  <PackageInstallInstructions packageName="dagster-postgres dagster-postgres-pandas" />

- **A PostgreSQL database** reachable from your Dagster code, and a role allowed to create schemas and tables in it.

## Step 1: Configure the I/O manager

Add <PyObject section="libraries" integration="postgres" module="dagster_postgres_pandas" object="PostgresPandasIOManager" /> to your `Definitions`. You can pass a full connection URL, or the individual connection fields:

```python
from dagster import Definitions, EnvVar
from dagster_postgres_pandas import PostgresPandasIOManager

defs = Definitions(
    assets=[...],
    resources={
        "io_manager": PostgresPandasIOManager(
            # either a full URL ...
            postgres_url=EnvVar("DAGSTER_PG_URL"),
            # ... or the individual parts:
            # hostname="localhost",
            # username="postgres",
            # password=EnvVar("PG_PASSWORD"),
            # db_name="analytics",
            # port=5432,
            schema="analytics",  # default schema for assets without one
        )
    },
)
```

The `schema` option is optional. When it is not set, the I/O manager uses the asset's `key_prefix` or `schema` metadata, and falls back to `public`.

## Step 2: Store and load DataFrames

Return a Pandas DataFrame from an asset to store it. The asset name becomes the table name, and the asset's `key_prefix` (or `schema` metadata) becomes the schema. Downstream assets that accept a `pd.DataFrame` parameter load the table back:

```python
import pandas as pd
from dagster import asset


@asset(key_prefix=["iris"])  # stored as the table iris.iris_dataset
def iris_dataset() -> pd.DataFrame:
    return pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=["sepal_length_cm", "sepal_width_cm", "petal_length_cm", "petal_width_cm", "species"],
    )


@asset(key_prefix=["iris"])
def iris_setosa(iris_dataset: pd.DataFrame) -> pd.DataFrame:
    return iris_dataset[iris_dataset["species"] == "Iris-setosa"]
```

Each materialization replaces the previous contents of the table. The schema is created if it does not exist, and the table is created on the first write with column types inferred by Pandas.

To load only some columns of an upstream table, add `columns` metadata to the input:

```python
from dagster import AssetIn, asset


@asset(
    key_prefix=["iris"],
    ins={"iris_dataset": AssetIn(metadata={"columns": ["sepal_length_cm", "species"]})},
)
def sepal_lengths(iris_dataset: pd.DataFrame) -> pd.DataFrame:
    return iris_dataset
```

## Step 3: Partitioned assets

For [partitioned assets](/guides/build/partitions-and-backfills), add `partition_expr` metadata naming the column that holds the partition value. Materializing a partition deletes only the rows of that partition before writing the new ones, and loading a partitioned input selects only the requested partitions:

```python
import pandas as pd
from dagster import AssetExecutionContext, DailyPartitionsDefinition, asset


@asset(
    key_prefix=["events"],
    partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"),
    metadata={"partition_expr": "event_date"},
)
def daily_events(context: AssetExecutionContext) -> pd.DataFrame:
    partition_date = pd.Timestamp(context.partition_key)
    return pd.DataFrame({"event_date": [partition_date] * 3, "value": [1, 2, 3]})
```

Time-window partitions are compared against the partition column as timestamps, static and dynamic partitions as string values. Multi-partitioned assets take a mapping of dimension name to column in `partition_expr`.

## Ops

For ops, the schema can be set with a `schema` entry in the output metadata; it defaults to `public`:

```python
import pandas as pd
from dagster import Out, op


@op(out=Out(metadata={"schema": "staging"}))
def make_table() -> pd.DataFrame:
    return pd.DataFrame({"a": [1, 2, 3]})
```

## Custom type handlers

<PyObject section="libraries" integration="postgres" module="dagster_postgres" object="PostgresIOManager" /> in `dagster-postgres` is the base class. Subclass it and return your own handlers from `type_handlers` to store other in-memory types in PostgreSQL alongside Pandas DataFrames.
