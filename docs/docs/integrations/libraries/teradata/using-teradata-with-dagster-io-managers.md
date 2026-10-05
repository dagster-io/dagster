---
title: 'Using Teradata with Dagster I/O managers'
description: 'Learn to integrate Teradata Vantage with Dagster using the Teradata I/O managers for pandas, polars and PySpark DataFrames.'
sidebar_position: 100
---

This tutorial focuses on how to store and load Dagster's [asset definitions](/guides/build/assets/defining-assets) in Teradata Vantage by using a Teradata I/O manager. An [**I/O manager**](/guides/build/io-managers) transfers the responsibility of storing and loading DataFrames as Teradata tables to Dagster.

By the end of the tutorial, you will:

- Configure a Teradata I/O manager
- Create a table in Teradata using a Dagster asset
- Make an existing Teradata table available in Dagster
- Load Teradata tables in downstream assets

This guide focuses on storing and loading pandas DataFrames in Teradata, but `dagster-teradata` also ships I/O managers for polars and PySpark DataFrames. The concepts from this guide apply to all three, and you can learn more about the polars and PySpark I/O managers in the [Teradata reference](/integrations/libraries/teradata/teradata-reference#using-the-teradata-io-manager).

**Prefer to use resources instead?** Unlike an I/O manager, resources allow you to run SQL queries directly against tables within an asset's compute function. For details, see [Dagster & Teradata](/integrations/libraries/teradata).

## Prerequisites

To complete this tutorial, you'll need:

- **Python 3.10 or higher.**

- **To install the `dagster-teradata` library with the `pandas` extra**:

  <PackageInstallInstructions packageName="dagster-teradata[pandas]" />

- **Access to a Teradata Vantage instance** and a user that can create tables.

  :::note

  If you need a test instance of Vantage, you can provision one for free at [https://clearscape.teradata.com](https://clearscape.teradata.com/sign-in?utm_source=dev_portal&utm_medium=quickstart_tutorial&utm_campaign=quickstarts)

  :::

- **An existing Teradata database** to store the tables in. The I/O manager does not create databases, since Teradata requires an explicit `PERM` space allocation:

  ```sql
  CREATE DATABASE analytics AS PERM = 1000000000;
  GRANT ALL ON analytics TO my_user;
  ```

- **To gather your connection details**. The Teradata I/O manager reads them from environment variables. In this guide we store them as follows:

  ```shell
  export TERADATA_HOST=<your Vantage host>
  export TERADATA_USER=<your username>
  export TERADATA_PASSWORD=<your password>
  export TERADATA_DATABASE=analytics
  ```

  Refer to the [Using environment variables and secrets guide](/guides/operate/configuration/using-environment-variables-and-secrets) for more info.

## Step 1: Configure the Teradata I/O manager

The Teradata I/O manager connects through a `TeradataResource`, so every connection option it supports (port, `logmech`, TLS, proxies, and so on) applies to the I/O manager as well. `host`, `user` and `password` are required. You can also specify a default `database` on the resource and, optionally, a `schema` on the I/O manager to override it.

```python
from dagster import Definitions, EnvVar
from dagster_teradata import TeradataPandasIOManager, TeradataResource

teradata = TeradataResource(
    host=EnvVar("TERADATA_HOST"),
    user=EnvVar("TERADATA_USER"),
    password=EnvVar("TERADATA_PASSWORD"),
    database=EnvVar("TERADATA_DATABASE"),
)

defs = Definitions(
    assets=[iris_dataset],
    resources={
        "io_manager": TeradataPandasIOManager(teradata=teradata),
    },
)
```

With this configuration, if you materialized an asset called `iris_dataset`, the Teradata I/O manager would store the data in the `analytics.iris_dataset` table.

In the <PyObject section="definitions" module="dagster" object="Definitions" /> object, we assign the `TeradataPandasIOManager` to the `io_manager` key. `io_manager` is a reserved key to set the default I/O manager for your assets.

:::note

Teradata has no separate schema level inside a database: a database **is** the schema, so table names are always two-part `database.table`. Dagster's `schema` concept maps onto the Teradata database.

:::

## Step 2: Create tables in Teradata

The Teradata I/O manager can create and update tables for your Dagster-defined assets, but you can also make existing Teradata tables available to Dagster.

<Tabs>

<TabItem value="Create tables in Teradata from Dagster assets">

### Store a Dagster asset as a table in Teradata

To store data in Teradata using the Teradata I/O manager, the definitions of your assets don't need to change. You can tell Dagster to use the Teradata I/O manager, like in [Step 1: Configure the Teradata I/O manager](#step-1-configure-the-teradata-io-manager), and Dagster will handle storing and loading your assets in Teradata.

```python
import pandas as pd
from dagster import asset


@asset
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

In this example, we first define our [asset](/guides/build/assets/defining-assets). Here, we are fetching the Iris dataset as a pandas DataFrame. The type signature of the function tells the I/O manager what data type it is working with, so it is important to include the return type `pd.DataFrame`.

When Dagster materializes the `iris_dataset` asset using the configuration from [Step 1: Configure the Teradata I/O manager](#step-1-configure-the-teradata-io-manager), the Teradata I/O manager will create the table `analytics.iris_dataset` if it does not exist and replace the contents of the table with the value returned from the `iris_dataset` asset. Column types are derived from the DataFrame's dtypes; see [Configuring the DataFrame handlers](/integrations/libraries/teradata/teradata-reference#configuring-the-dataframe-handlers) to pin them explicitly.

</TabItem>

<TabItem value="Make an existing table available in Dagster">

You may already have tables in Teradata that you want to make available to other Dagster assets. You can define [external assets](/guides/build/assets/external-assets) for these tables. By defining an external asset for the existing table, you tell Dagster how to find the table so it can be fetched for downstream assets.

```python
from dagster import AssetSpec

iris_harvest_data = AssetSpec(key="iris_harvest_data")
```

In this example, we create an `AssetSpec` for a pre-existing table - perhaps created by an external data ingestion tool - that contains data about iris harvests. To make the data available to other Dagster assets, we need to tell the Teradata I/O manager how to find the data.

Since we supply the database on the `TeradataResource` in [Step 1: Configure the Teradata I/O manager](#step-1-configure-the-teradata-io-manager), we only need to provide the table name. We do this with the `key` parameter in `AssetSpec`. When the I/O manager needs to load `iris_harvest_data` in a downstream asset, it will select the data in the `analytics.iris_harvest_data` table as a pandas DataFrame and provide it to the downstream asset.

</TabItem>
</Tabs>

## Step 3: Load Teradata tables in downstream assets

Once you have created an asset that represents a table in Teradata, you will likely want to create additional assets that work with the data. Dagster and the Teradata I/O manager allow you to load the data stored in Teradata tables into downstream assets.

```python
import pandas as pd
from dagster import asset


@asset
def iris_cleaned(iris_dataset: pd.DataFrame) -> pd.DataFrame:
    return iris_dataset.dropna().drop_duplicates()
```

In this example, we want to provide the `iris_dataset` asset from the [Store a Dagster asset as a table in Teradata](#store-a-dagster-asset-as-a-table-in-teradata) example to the `iris_cleaned` asset. In `iris_cleaned`, the `iris_dataset` parameter tells Dagster that the value for the `iris_dataset` asset should be provided as input to `iris_cleaned`.

When materializing these assets, Dagster will use the `TeradataPandasIOManager` to fetch `analytics.iris_dataset` as a pandas DataFrame and pass this DataFrame as the `iris_dataset` parameter to `iris_cleaned`. When `iris_cleaned` returns a pandas DataFrame, Dagster will use the `TeradataPandasIOManager` to store the DataFrame as the `analytics.iris_cleaned` table in Teradata.

## Completed code example

When finished, your code should look like the following:

```python
import pandas as pd
from dagster import AssetSpec, Definitions, EnvVar, asset
from dagster_teradata import TeradataPandasIOManager, TeradataResource

iris_harvest_data = AssetSpec(key="iris_harvest_data")


@asset
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


@asset
def iris_cleaned(iris_dataset: pd.DataFrame) -> pd.DataFrame:
    return iris_dataset.dropna().drop_duplicates()


defs = Definitions(
    assets=[iris_dataset, iris_harvest_data, iris_cleaned],
    resources={
        "io_manager": TeradataPandasIOManager(
            teradata=TeradataResource(
                host=EnvVar("TERADATA_HOST"),
                user=EnvVar("TERADATA_USER"),
                password=EnvVar("TERADATA_PASSWORD"),
                database=EnvVar("TERADATA_DATABASE"),
            ),
        )
    },
)
```

To use polars or PySpark instead, swap `TeradataPandasIOManager` for `TeradataPolarsIOManager` or `TeradataPySparkIOManager` and change the type annotations accordingly. See the [Teradata reference](/integrations/libraries/teradata/teradata-reference#storing-and-loading-polars-dataframes-in-teradata) for details.
