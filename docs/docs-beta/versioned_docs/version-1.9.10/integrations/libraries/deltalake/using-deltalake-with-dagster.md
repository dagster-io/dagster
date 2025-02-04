---
title: "Using Delta Lake with Dagster"
description: Store your Dagster assets in a Delta Lake
sidebar_position: 100
---

This tutorial focuses on how to store and load Dagster [asset definitions](/guides/build/assets/defining-assets) in a Delta Lake.

By the end of the tutorial, you will:

- Configure a Delta Lake I/O manager
- Create a table in Delta Lake using a Dagster asset
- Make a Delta Lake table available in Dagster
- Load Delta tables in downstream assets

While this guide focuses on storing and loading Pandas DataFrames in Delta Lakes, Dagster also supports using PyArrow Tables and Polars DataFrames. Learn more about setting up and using the Delta Lake I/O manager with PyArrow Tables and Polars DataFrames in the [Delta Lake reference](reference).

## Prerequisites

To complete this tutorial, you'll need to install the `dagster-deltalake` and `dagster-deltalake-pandas` libraries:

```shell
pip install dagster-deltalake dagster-deltalake-pandas
```

## Step 1: Configure the Delta Lake I/O manager

The Delta Lake I/O manager requires some configuration to set up your Delta Lake. You must provide a root path where your Delta tables will be created. Additionally, you can specify a `schema` where the Delta Lake I/O manager will create tables.

<CodeExample path="docs_snippets/docs_snippets/integrations/deltalake/configuration.py" startAfter="start_example" endBefore="end_example" />

With this configuration, if you materialized an asset called `iris_dataset`, the Delta Lake I/O manager would store the data within a folder `iris/iris_dataset` under the provided root directory `path/to/deltalake`.

Finally, in the <PyObject section="definitions" module="dagster" object="Definitions" /> object, we assign the <PyObject section="libraries" module="dagster_deltalake_pandas" object="DeltaLakePandasIOManager" /> to the `io_manager` key. `io_manager` is a reserved key to set the default I/O manager for your assets.

## Step 2: Create Delta Lake tables

The Delta Lake I/O manager can create and update tables for your Dagster-defined assets, but you can also make existing Delta Lake tables available to Dagster.

<Tabs>

<TabItem value="Create Delta tables from Dagster assets">

**Store a Dagster asset as a table in Delta Lake**

To store data in Delta Lake using the Delta Lake I/O manager, the definitions of your assets don't need to change. You can tell Dagster to use the Delta Lake I/O manager, like in [Step 1](#step-1-configure-the-delta-lake-io-manager), and Dagster will handle storing and loading your assets in Delta Lake.

<CodeExample path="docs_snippets/docs_snippets/integrations/deltalake/basic_example.py" />

In this example, we first define an [asset](/guides/build/assets/defining-assets). Here, we fetch the Iris dataset as a Pandas DataFrame and rename the columns. The type signature of the function tells the I/O manager what data type it is working with, so it's important to include the return type `pd.DataFrame`.

When Dagster materializes the `iris_dataset` asset using the configuration from [Step 1](#step-1-configure-the-delta-lake-io-manager), the Delta Lake I/O manager will create the table `iris/iris_dataset` if it doesn't exist and replace the contents of the table with the value returned from the `iris_dataset` asset.

</TabItem>

<TabItem value="Make existing tables available in Dagster">

### Make an existing table available in Dagster

If you already have tables in your Delta Lake, you may want to make them available to other Dagster assets. You can accomplish this by defining [external assets](/guides/build/assets/external-assets) for these tables. By creating an external asset for the existing table, you tell Dagster how to find the table so it can be fetched for downstream assets.

<CodeExample path="docs_snippets/docs_snippets/integrations/deltalake/source_asset.py" />

In this example, we create a <PyObject section="assets" module="dagster" object="AssetSpec" /> for an existing table containing iris harvest data. To make the data available to other Dagster assets, we need to tell the Delta Lake I/O manager how to find the data.

Because we already supplied the database and schema in the I/O manager configuration in [Step 1](#step-1-configure-the-delta-lake-io-manager), we only need to provide the table name. We do this with the `key` parameter in `AssetSpec`. When the I/O manager needs to load the `iris_harvest_data` in a downstream asset, it will select the data in the `iris/iris_harvest_data` folder as a Pandas DataFrame and provide it to the downstream asset.

</TabItem>
</Tabs>

## Step 3: Load Delta Lake tables in downstream assets

Once you've created an asset that represents a table in your Delta Lake, you will likely want to create additional assets that work with the data. Dagster and the Delta Lake I/O manager allow you to load the data stored in Delta tables into downstream assets.

<CodeExample path="docs_snippets/docs_snippets/integrations/deltalake/load_downstream.py" startAfter="start_example" endBefore="end_example" />

In this example, we want to provide the `iris_dataset` asset to the `iris_cleaned` asset. Refer to the Store a Dagster asset as a table in Delta Lake example in [step 2](#step-2-create-delta-lake-tables) for a look at the `iris_dataset` asset.

In `iris_cleaned`, the `iris_dataset` parameter tells Dagster that the value for the `iris_dataset` asset should be provided as input to `iris_cleaned`. If this feels too magical for you, refer to the docs for explicitly specifying dependencies.

When materializing these assets, Dagster will use the `DeltaLakePandasIOManager` to fetch the `iris/iris_dataset` as a Pandas DataFrame and pass the DataFrame as the `iris_dataset` parameter to `iris_cleaned`. When `iris_cleaned` returns a Pandas DataFrame, Dagster will use the `DeltaLakePandasIOManager` to store the DataFrame as the `iris/iris_cleaned` table in your Delta Lake.

## Completed code example

When finished, your code should look like the following:

<CodeExample path="docs_snippets/docs_snippets/integrations/deltalake/full_example.py" />

## Related

For more Delta Lake features, refer to the [Delta Lake reference](reference).

For more information on asset definitions, see the [Assets documentation](/guides/build/assets/defining-assets).

For more information on I/O managers, refer to the [I/O manager documentation](/guides/build/io-managers/).
