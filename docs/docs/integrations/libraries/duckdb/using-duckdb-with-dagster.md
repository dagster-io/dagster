---
title: "Using DuckDB with Dagster"
description: Store your Dagster assets in DuckDB
sidebar_position: 100
---

This tutorial focuses on creating and interacting with DuckDB tables using Dagster's [asset definitions](/guides/build/assets/defining-assets).

The `dagster-duckdb` library provides two ways to interact with DuckDB tables:

- [Resource](/guides/build/external-resources/): The resource allows you to directly run SQL queries against tables within an asset's compute function. Available resources: <PyObject section="libraries" module="dagster_duckdb" object="DuckDBResource" />.
- [I/O manager](/guides/build/io-managers/): The I/O manager transfers the responsibility of storing and loading DataFrames as DuckdB tables to Dagster. Available I/O managers: <PyObject section="libraries" module="dagster_duckdb_pandas" object="DuckDBPandasIOManager" />, <PyObject section="libraries" module="dagster_duckdb_pyspark" object="DuckDBPySparkIOManager" />, <PyObject section="libraries" module="dagster_duckdb_polars" object="DuckDBPolarsIOManager" />.

This tutorial is divided into two sections to demonstrate the differences between the DuckDB resource and the DuckDB I/O manager. Each section will create the same assets, but the first section will use the DuckDB resource to store data in DuckDB, whereas the second section will use the DuckDB I/O manager. When writing your own assets, you may choose one or the other (or both) approaches depending on your storage requirements. {/* TODO fix link See [When to use I/O managers](/guides/build/io-managers/#when-to-use-io-managers) to learn more about when to use I/O managers and when to use resources. */}

In [Option 1](#option-1-using-the-duckdb-resource) you will:

- Set up and configure the DuckDB resource.
- Use the DuckDB resource to execute a SQL query to create a table.
- Use the DuckDB resource to execute a SQL query to interact with the table.

In [Option 2](#option-2-using-the-duckdb-io-manager) you will:

- Set up and configure the DuckDB I/O manager.
- Use Pandas to create a DataFrame, then delegate responsibility creating a table to the DuckDB I/O manager.
- Use the DuckDB I/O manager to load the table into memory so that you can interact with it using the Pandas library.

When writing your own assets, you may choose one or the other (or both) approaches depending on your storage requirements. {/* See [When to use I/O managers](/guides/build/io-managers/#when-to-use-io-managers) to learn more. */}

By the end of the tutorial, you will:

- Understand how to interact with a DuckDB database using the DuckDB resource.
- Understand how to use the DuckDB I/O manager to store and load DataFrames as DuckDB tables.
- Understand how to define dependencies between assets corresponding to tables in a DuckDB database.

## Prerequisites

To complete this tutorial, you'll need:

- **To install the `dagster-duckdb` and `dagster-duckdb-pandas` libraries**:

  ```shell
  pip install dagster-duckdb dagster-duckdb-pandas
  ```

## Option 1: Using the DuckDB resource

### Step 1: Configure the DuckDB resource

To use the DuckDB resource, you'll need to add it to your `Definitions` object. The DuckDB resource requires some configuration. You must set a path to a DuckDB database as the `database` configuration value. If the database does not already exist, it will be created for you:

<CodeExample path="docs_snippets/docs_snippets/integrations/duckdb/tutorial/resource/configuration.py" startAfter="start_example" endBefore="end_example" />

### Step 2: Create tables in DuckDB \{#option-1-step-2}

<Tabs>

<TabItem value="Create DuckDB tables in Dagster">

**Create DuckDB tables in Dagster**

Using the DuckDB resource, you can create DuckDB tables using the DuckDB Python API:

<CodeExample path="docs_snippets/docs_snippets/integrations/duckdb/tutorial/resource/create_table.py" startAfter="start_example" endBefore="end_example" />

In this example, you're defining an asset that fetches the Iris dataset as a Pandas DataFrame and renames the columns. Then, using the DuckDB resource, the DataFrame is stored in DuckDB as the `iris.iris_dataset` table.

</TabItem>

<TabItem value="Making Dagster aware of existing tables">

**Making Dagster aware of existing tables**

If you already have existing tables in DuckDB and other assets defined in Dagster depend on those tables, you may want Dagster to be aware of those upstream dependencies. Making Dagster aware of these tables will allow you to track the full data lineage in Dagster. You can accomplish this by defining [external assets](/guides/build/assets/external-assets) for these tables.


<CodeExample path="docs_snippets/docs_snippets/integrations/duckdb/tutorial/io_manager/source_asset.py" />

In this example, you're creating a <PyObject section="assets" module="dagster" object="AssetSpec" /> for a pre-existing table called `iris_harvest_data`.

</TabItem>

</Tabs>

Now you can run `dagster dev` and materialize the `iris_dataset` asset from the Dagster UI.

### Step 3: Define downstream assets

Once you have created an asset that represents a table in DuckDB, you will likely want to create additional assets that work with the data.

<CodeExample path="docs_snippets/docs_snippets/integrations/duckdb/tutorial/resource/downstream.py" startAfter="start_example" endBefore="end_example" />

In this asset, you're creating second table that only contains the data for the _Iris Setosa_ species. This asset has a dependency on the `iris_dataset` asset. To define this dependency, you provide the `iris_dataset` asset as the `deps` parameter to the `iris_setosa` asset. You can then run the SQL query to create the table of _Iris Setosa_ data.

### Completed code example

When finished, your code should look like the following:

<CodeExample path="docs_snippets/docs_snippets/integrations/duckdb/tutorial/resource/full_example.py" />

## Option 2: Using the DuckDB I/O manager

You may want to use an I/O manager to handle storing DataFrames as tables in DuckDB and loading DuckDB tables as DataFrames in downstream assets. You may want to use an I/O manager if:

- You want your data to be loaded in memory so that you can interact with it using Python.
- You'd like to have Dagster manage how you store the data and load it as an input in downstream assets.

{/* Using an I/O manager is not required, and you can reference [When to use I/O managers](/guides/build/io-managers/#when-to-use-io-managers) to learn more. */}

This section of the guide focuses on storing and loading Pandas DataFrames in DuckDB, but Dagster also supports using PySpark and Polars DataFrames with DuckDB. The concepts from this guide apply to working with PySpark and Polars DataFrames, and you can learn more about setting up and using the DuckDB I/O manager with PySpark and Polars DataFrames in the [reference guide](reference).

### Step 1: Configure the DuckDB I/O manager

To use the DuckDB I/O, you'll need to add it to your `Definitions` object. The DuckDB I/O manager requires some configuration to connect to your database. You must provide a path where a DuckDB database will be created. Additionally, you can specify a `schema` where the DuckDB I/O manager will create tables.

<CodeExample path="docs_snippets/docs_snippets/integrations/duckdb/tutorial/io_manager/configuration.py" startAfter="start_example" endBefore="end_example" />

### Step 2: Create tables in DuckDB \{#option-2-step-2}

The DuckDB I/O manager can create and update tables for your Dagster-defined assets, but you can also make existing DuckDB tables available to Dagster.

<Tabs>

<TabItem value="Create tables in DuckDB from Dagster assets">

#### Store a Dagster asset as a table in DuckDB

To store data in DuckDB using the DuckDB I/O manager, you can simply return a Pandas DataFrame from your asset. Dagster will handle storing and loading your assets in DuckDB.

<CodeExample path="docs_snippets/docs_snippets/integrations/duckdb/tutorial/io_manager/basic_example.py" />

In this example, you're defining an asset that fetches the Iris dataset as a Pandas DataFrame, renames the columns, then returns the DataFrame. The type signature of the function tells the I/O manager what data type it is working with, so it is important to include the return type `pd.DataFrame`.

When Dagster materializes the `iris_dataset` asset using the configuration from [Step 1: Configure the DuckDB I/O manager](#step-1-configure-the-duckdb-io-manager), the DuckDB I/O manager will create the table `IRIS.IRIS_DATASET` if it does not exist and replace the contents of the table with the value returned from the `iris_dataset` asset.

</TabItem>

<TabItem value="Make existing tables available in Dagster">

**Make an existing table available in Dagster**

If you already have existing tables in DuckDB and other assets defined in Dagster depend on those tables, you may want Dagster to be aware of those upstream dependencies. Making Dagster aware of these tables will allow you to track the full data lineage in Dagster. You can accomplish this by defining [external assets](/guides/build/assets/external-assets) for these tables.

<CodeExample path="docs_snippets/docs_snippets/integrations/duckdb/tutorial/io_manager/source_asset.py" />

In this example, you're creating a <PyObject section="assets" module="dagster" object="AssetSpec" /> for a pre-existing table containing iris harvests data. To make the data available to other Dagster assets, you need to tell the DuckDB I/O manager how to find the data.

Because you already supplied the database and schema in the I/O manager configuration in [Step 1: Configure the DuckDB I/O manager](#step-1-configure-the-duckdb-io-manager), you only need to provide the table name. This is done with the `key` parameter in `AssetSpec`. When the I/O manager needs to load the `iris_harvest_data` in a downstream asset, it will select the data in the `IRIS.IRIS_HARVEST_DATA` table as a Pandas DataFrame and provide it to the downstream asset.

</TabItem>
</Tabs>

### Step 3: Load DuckDB tables in downstream assets

Once you have created an asset that represents a table in DuckDB, you will likely want to create additional assets that work with the data. Dagster and the DuckDB I/O manager allow you to load the data stored in DuckDB tables into downstream assets.

<CodeExample path="docs_snippets/docs_snippets/integrations/duckdb/tutorial/io_manager/load_downstream.py" startAfter="start_example" endBefore="end_example" />

In this asset, you're providing the `iris_dataset` asset as a dependency to `iris_setosa`. By supplying `iris_dataset` as a parameter to `iris_setosa`, Dagster knows to use the `DuckDBPandasIOManager` to load this asset into memory as a Pandas DataFrame and pass it as an argument to `iris_setosa`. Next, a DataFrame that only contains the data for the _Iris Setosa_ species is created and returned. Then the `DuckDBPandasIOManager` will store the DataFrame as the `IRIS.IRIS_SETOSA` table in DuckDB.

### Completed code example

When finished, your code should look like the following:

<CodeExample path="docs_snippets/docs_snippets/integrations/duckdb/tutorial/io_manager/full_example.py" />

## Related

For more DuckDB features, refer to the [DuckDB reference](reference).

For more information on asset definitions, see the [Assets documentation](/guides/build/assets/).

For more information on I/O managers, see the [I/O manager documentation](/guides/build/io-managers/).
