---
title: "Using Snowflake with Dagster resources"
description: "Learn to integrate Snowflake with Dagster using a Snowflake resource."
sidebar_position: 200
---

This tutorial focuses on how to store and load Dagster's [asset definitions](/guides/build/assets/defining-assets) in Snowflake by using Dagster's <PyObject section="libraries" object="SnowflakeResource" module="dagster_snowflake" />. A [**resource**](/guides/build/external-resources/) allows you to directly run SQL queries against tables within an asset's compute function.

By the end of the tutorial, you will:

- Configure a Snowflake resource
- Use the Snowflake resource to execute a SQL query that creates a table
- Load Snowflake tables in downstream assets
- Add the assets and Snowflake resource to a `Definitions` object

**Prefer to use an I/O manager?** Unlike resources, an [I/O manager](/guides/build/io-managers/) transfers the responsibility of storing and loading DataFrames as Snowflake tables to Dagster. Refer to the [Snowlake I/O manager guide](using-snowflake-with-dagster-io-managers) for more info.

## Prerequisites

To complete this tutorial, you'll need:

- **To install the following libraries**:

  ```shell
  pip install dagster dagster-snowflake pandas
  ```

- **To gather the following information**, which is required to use the Snowflake resource:

  - **Snowflake account name**: You can find this by logging into Snowflake and getting the account name from the URL:
    
    ![Snowflake account name in URL](/images/integrations/snowflake/snowflake-account.png)

  - **Snowflake credentials**: You can authenticate with Snowflake two ways: with a username and password or with a username and private key.

    The Snowflake resource can read these authentication values from environment variables. In this guide, we use password authentication and store the username and password as `SNOWFLAKE_USER` and `SNOWFLAKE_PASSWORD`, respectively:

    ```shell
    export SNOWFLAKE_USER=<your username>
    export SNOWFLAKE_PASSWORD=<your password>
    ```

    Refer to the [Using environment variables and secrets guide](/guides/deploy/using-environment-variables-and-secrets) for more info.

    For more information on authenticating with a private key, see [Authenticating with a private key](reference#authenticating-using-a-private-key) in the Snowflake reference guide.


## Step 1: Configure the Snowflake resource

To connect to Snowflake, we'll use the `dagster-snowflake` <PyObject section="libraries" object="SnowflakeResource" module="dagster_snowflake" />. The <PyObject section="libraries" object="SnowflakeResource" module="dagster_snowflake" /> requires some configuration:

- **The `account` and `user` values are required.**
- **One method of authentication is required**, either by using a password or a private key.
- **Optional**: Using the `warehouse`, `schema`, and `role` attributes, you can specify where data should be stored and a `role` for the resource to use.

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/resource_tutorial/full_example.py" startAfter="start_config" endBefore="end_config" />

With this configuration, if you materialized an asset named `iris_dataset`, <PyObject section="libraries" object="SnowflakeResource" module="dagster_snowflake" /> would use the role `WRITER` and store the data in the `FLOWERS.IRIS.IRIS_DATASET` table using the `PLANTS` warehouse.

For more info about each of the configuration values, refer to the <PyObject section="libraries" module="dagster_snowflake" object="SnowflakeResource" /> API documentation.

## Step 2: Create tables in Snowflake

<Tabs>
<TabItem value="Create tables in Snowflake from Dagster assets">

Using the Snowflake resource, you can create Snowflake tables using the Snowflake Python API:

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/resource_tutorial/full_example.py" startAfter="start_asset" endBefore="end_asset" />

In this example, we've defined an asset that fetches the Iris dataset as a Pandas DataFrame. Then, using the Snowflake resource, the DataFrame is stored in Snowflake as the `FLOWERS.IRIS.IRIS_DATASET` table.

</TabItem>
<TabItem value="Make existing tables available in Dagster">

If you have existing tables in Snowflake and other assets defined in Dagster depend on those tables, you may want Dagster to be aware of those upstream dependencies.

Making Dagster aware of these tables allows you to track the full data lineage in Dagster. You can accomplish this by defining [external assets](/guides/build/assets/external-assets) for these tables. For example:

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/source_asset.py" />

In this example, we created a <PyObject section="assets" module="dagster" object="AssetSpec" /> for a pre-existing table called `iris_harvest_data`.

Since we supplied the database and the schema in the resource configuration in [Step 1](#step-1-configure-the-snowflake-resource), we only need to provide the table name. We did this by using the `key` parameter in our <PyObject section="assets" module="dagster" object="AssetSpec" />. When the `iris_harvest_data` asset needs to be loaded in a downstream asset, the data in the `FLOWERS.IRIS.IRIS_HARVEST_DATA` table will be selected and provided to the asset.

</TabItem>
</Tabs>

## Step 3: Define downstream assets

Once you've created an asset that represents a table in Snowflake, you may want to create additional assets that work with the data. In the following example, we've defined an asset that creates a second table, which contains only the data for the _Iris Setosa_ species:

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/resource_tutorial/full_example.py" startAfter="start_downstream" endBefore="end_downstream" />

To accomplish this, we defined a dependency on the `iris_dataset` asset using the `deps` parameter. Then, the SQL query runs and creates the table of _Iris Setosa_ data.

## Step 4: Definitions object

The last step is to add the <PyObject section="libraries" object="SnowflakeResource" module="dagster_snowflake" /> and the assets to the project's <PyObject section="definitions" module="dagster" object="Definitions" /> object:

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/resource_tutorial/full_example.py" startAfter="start_definitions" endBefore="end_definitions" />

This makes the resource and assets available to Dagster tools like the UI and CLI.

## Completed code example

When finished, your code should look like the following:

{/* TODO convert to CodeExample when 'lines' property implemented */}
```python file=docs_snippets/docs_snippets/integrations/snowflake/resource_tutorial/full_example.py lines=1,4-16,27-58,67-80,86-88
import pandas as pd
from dagster_snowflake import SnowflakeResource
from snowflake.connector.pandas_tools import write_pandas

from dagster import Definitions, EnvVar, MaterializeResult, asset

snowflake = SnowflakeResource(
    account=EnvVar("SNOWFLAKE_ACCOUNT"),  # required
    user=EnvVar("SNOWFLAKE_USER"),  # required
    password=EnvVar("SNOWFLAKE_PASSWORD"),  # password or private key required
    warehouse="PLANTS",
    schema="IRIS",
    role="WRITER",
)


@asset
def iris_dataset(snowflake: SnowflakeResource):
    iris_df = pd.read_csv(
        "https://docs.dagster.io/assets/iris.csv",
        names=[
            "sepal_length_cm",
            "species",
        ],
    )

    with snowflake.get_connection() as conn:
        table_name = "iris_dataset"
        database = "flowers"
        schema = "iris"
        success, number_chunks, rows_inserted, output = write_pandas(
            conn,
            iris_df,
            table_name=table_name,
            database=database,
            schema=schema,
            auto_create_table=True,
            overwrite=True,
            quote_identifiers=False,
        )

    return MaterializeResult(
        metadata={"rows_inserted": rows_inserted},
    )


@asset(deps=["iris_dataset"])
def iris_setosa(snowflake: SnowflakeResource) -> None:
    query = """
        create or replace table iris.iris_setosa as (
            SELECT *
            FROM iris.iris_dataset
            WHERE species = 'Iris-setosa'
        );
    """

    with snowflake.get_connection() as conn:
        conn.cursor.execute(query)


defs = Definitions(
    assets=[iris_dataset, iris_setosa], resources={"snowflake": snowflake}
)
```
