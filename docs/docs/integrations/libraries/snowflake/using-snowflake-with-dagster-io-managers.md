---
title: "Using Snowflake with with Dagster I/O managers"
description: "Learn to integrate Snowflake with Dagster using a Snowflake I/O manager."
sidebar_position: 100
---

This tutorial focuses on how to store and load Dagster's [asset definitions](/guides/build/assets/defining-assets) in Snowflake by using a Snowflake I/O manager. An [**I/O manager**](/guides/build/io-managers/) transfers the responsibility of storing and loading DataFrames as Snowflake tables to Dagster.

By the end of the tutorial, you will:

- Configure a Snowflake I/O manager
- Create a table in Snowflake using a Dagster asset
- Make a Snowflake table available in Dagster
- Load Snowflake tables in downstream assets

This guide focuses on storing and loading Pandas DataFrames in Snowflake, but Dagster also supports using PySpark DataFrames with Snowflake. The concepts from this guide apply to working with PySpark DataFrames, and you can learn more about setting up and using the Snowflake I/O manager with PySpark DataFrames in the [Snowflake reference](reference).

**Prefer to use resources instead?** Unlike an I/O manager, resources allow you to run SQL queries directly against tables within an asset's compute function. For details, see "[Using Snowlake with Dagster resources](using-snowflake-with-dagster)".

## Prerequisites

To complete this tutorial, you'll need:

- **To install the `dagster-snowflake` and `dagster-snowflake-pandas` libraries**:

  ```shell
  pip install dagster-snowflake dagster-snowflake-pandas
  ```

- **To gather the following information**, which is required to use the Snowflake I/O manager:

  - **Snowflake account name**: You can find this by logging into Snowflake and getting the account name from the URL:

    ![Snowflake account name from URL](/images/integrations/snowflake/snowflake-account.png)

  - **Snowflake credentials**: You can authenticate with Snowflake two ways: with a username and password, or with a username and private key.

    The Snowflake I/O manager can read all of these authentication values from environment variables. In this guide, we use password authentication and store the username and password as `SNOWFLAKE_USER` and `SNOWFLAKE_PASSWORD`, respectively.

    ```shell
    export SNOWFLAKE_USER=<your username>
    export SNOWFLAKE_PASSWORD=<your password>
    ```

    Refer to the [Using environment variables and secrets guide](/guides/deploy/using-environment-variables-and-secrets) for more info.

    For more information on authenticating with a private key, see [Authenticating with a private key](reference#authenticating-using-a-private-key) in the Snowflake reference guide.


## Step 1: Configure the Snowflake I/O manager

The Snowflake I/O manager requires some configuration to connect to your Snowflake instance. The `account`, `user` are required to connect with Snowflake. One method of authentication is required. You can use a password or a private key. Additionally, you need to specify a `database` to where all the tables should be stored.

You can also provide some optional configuration to further customize the Snowflake I/O manager. You can specify a `warehouse` and `schema` where data should be stored, and a `role` for the I/O manager.

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/io_manager_tutorial/configuration.py" startAfter="start_example" endBefore="end_example" />

With this configuration, if you materialized an asset called `iris_dataset`, the Snowflake I/O manager would be permissioned with the role `writer` and would store the data in the `FLOWERS.IRIS.IRIS_DATASET` table in the `PLANTS` warehouse.

Finally, in the <PyObject section="definitions" module="dagster" object="Definitions" /> object, we assign the <PyObject section="libraries" module="dagster_snowflake_pandas" object="SnowflakePandasIOManager" /> to the `io_manager` key. `io_manager` is a reserved key to set the default I/O manager for your assets.

For more info about each of the configuration values, refer to the <PyObject section="libraries" module="dagster_snowflake_pandas" object="SnowflakePandasIOManager" /> API documentation.

## Step 2: Create tables in Snowflake

The Snowflake I/O manager can create and update tables for your Dagster defined assets, but you can also make existing Snowflake tables available to Dagster.

<Tabs>

<TabItem value="Create tables in Snowflake from Dagster assets">

### Store a Dagster asset as a table in Snowflake

To store data in Snowflake using the Snowflake I/O manager, the definitions of your assets don't need to change. You can tell Dagster to use the Snowflake I/O manager, like in [Step 1: Configure the Snowflake I/O manager](#step-1-configure-the-snowflake-io-manager), and Dagster will handle storing and loading your assets in Snowflake.

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/io_manager_tutorial/create_table.py" />

In this example, we first define our [asset](/guides/build/assets/defining-assets). Here, we are fetching the Iris dataset as a Pandas DataFrame and renaming the columns. The type signature of the function tells the I/O manager what data type it is working with, so it is important to include the return type `pd.DataFrame`.

When Dagster materializes the `iris_dataset` asset using the configuration from [Step 1: Configure the Snowflake I/O manager](#step-1-configure-the-snowflake-io-manager), the Snowflake I/O manager will create the table `FLOWERS.IRIS.IRIS_DATASET` if it does not exist and replace the contents of the table with the value returned from the `iris_dataset` asset.

</TabItem>

<TabItem value="Make an existing table available in Dagster">

You may already have tables in Snowflake that you want to make available to other Dagster assets. You can define [external assets](/guides/build/assets/external-assets) for these tables. By defining an external asset for the existing table, you tell Dagster how to find the table so it can be fetched for downstream assets.

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/source_asset.py" />

In this example, we create a <PyObject section="assets" module="dagster" object="AssetSpec" /> for a pre-existing table - perhaps created by an external data ingestion tool - that contains data about iris harvests. To make the data available to other Dagster assets, we need to tell the Snowflake I/O manager how to find the data.

Since we supply the database and the schema in the I/O manager configuration in [Step 1: Configure the Snowflake I/O manager](#step-1-configure-the-snowflake-io-manager), we only need to provide the table name. We do this with the `key` parameter in `AssetSpec`. When the I/O manager needs to load the `iris_harvest_data` in a downstream asset, it will select the data in the `FLOWERS.IRIS.IRIS_HARVEST_DATA` table as a Pandas DataFrame and provide it to the downstream asset.

</TabItem>
</Tabs>

## Step 3: Load Snowflake tables in downstream assets

Once you have created an asset that represents a table in Snowflake, you will likely want to create additional assets that work with the data. Dagster and the Snowflake I/O manager allow you to load the data stored in Snowflake tables into downstream assets.

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/io_manager_tutorial/downstream.py" startAfter="start_example" endBefore="end_example" />

In this example, we want to provide the `iris_dataset` asset from the [Store a Dagster asset as a table in Snowflake](#store-a-dagster-asset-as-a-table-in-snowflake) example to the `iris_cleaned` asset. In `iris_cleaned`, the `iris_dataset` parameter tells Dagster that the value for the `iris_dataset` asset should be provided as input to `iris_cleaned`.

When materializing these assets, Dagster will use the `SnowflakePandasIOManager` to fetch the `FLOWERS.IRIS.IRIS_DATASET` as a Pandas DataFrame and pass this DataFrame as the `iris_dataset` parameter to `iris_cleaned`. When `iris_cleaned` returns a Pandas DataFrame, Dagster will use the `SnowflakePandasIOManager` to store the DataFrame as the `FLOWERS.IRIS.IRIS_CLEANED` table in Snowflake.

## Completed code example

When finished, your code should look like the following:

<CodeExample path="docs_snippets/docs_snippets/integrations/snowflake/io_manager_tutorial/full_example.py" />
