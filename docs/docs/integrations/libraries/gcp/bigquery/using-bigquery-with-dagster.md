---
title: 'Using Google BigQuery with Dagster'
description: Store your Dagster assets in BigQuery
sidebar_position: 100
---

import Beta from '@site/docs/partials/\_Beta.md';

<Beta />

This tutorial focuses on creating and interacting with BigQuery tables using Dagster's [asset definitions](/guides/build/assets/defining-assets).

The `dagster-gcp` library provides two ways to interact with BigQuery tables:

- [Resource](/guides/build/external-resources/): The resource allows you to directly run SQL queries against tables within an asset's compute function. Available resources: <PyObject section="libraries" module="dagster_gcp" object="BigQueryResource" />
- [I/O manager](/guides/build/io-managers/): The I/O manager transfers the responsibility of storing and loading DataFrames as BigQuery tables to Dagster. Available I/O managers: <PyObject section="libraries" module="dagster_gcp_pandas" object="BigQueryPandasIOManager" />, <PyObject section="libraries" module="dagster_gcp_pyspark" object="BigQueryPySparkIOManager" />

This tutorial is divided into two sections to demonstrate the differences between the BigQuery resource and the BigQuery I/O manager. Each section will create the same assets, but the first section will use the BigQuery resource to store data in BigQuery, whereas the second section will use the BigQuery I/O manager. When writing your own assets, you may choose one or the other (or both) approaches depending on your storage requirements. {/* See [When to use I/O managers](/guides/build/io-managers/#when-to-use-io-managers) to learn more about when to use I/O managers and when to use resources. */}

In [Option 1](#option-1-using-the-bigquery-resource) you will:

- Set up and configure the BigQuery resource.
- Use the BigQuery resource to execute a SQL query to create a table.
- Use the BigQuery resource to execute a SQL query to interact with the table.

In [Option 2](#option-2-using-the-bigquery-io-manager) you will:

- Set up and configure the BigQuery I/O manager.
- Use Pandas to create a DataFrame, then delegate responsibility creating a table to the BigQuery I/O manager.
- Use the BigQuery I/O manager to load the table into memory so that you can interact with it using the Pandas library.

By the end of the tutorial, you will:

- Understand how to interact with a BigQuery database using the BigQuery resource.
- Understand how to use the BigQuery I/O manager to store and load DataFrames as BigQuery tables.
- Understand how to define dependencies between assets corresponding to tables in a BigQuery database.

## Prerequisites

To complete this tutorial, you'll need:

- **To install the `dagster-gcp` and `dagster-gcp-pandas` libraries**:

  ```shell
  pip install dagster-gcp dagster-gcp-pandas
  ```

- **To gather the following information**:

  - **Google Cloud Project (GCP) project name**: You can find this by logging into GCP and choosing one of the project names listed in the dropdown in the top left corner.

  - **GCP credentials**: You can authenticate with GCP two ways: by following GCP authentication instructions [here](https://cloud.google.com/docs/authentication/provide-credentials-adc), or by providing credentials directly to the BigQuery I/O manager.

    In this guide, we assume that you have run one of the `gcloud auth` commands or have set `GOOGLE_APPLICATION_CREDENTIALS` as specified in the linked instructions. For more information on providing credentials directly to the BigQuery resource and I/O manager, see [Providing credentials as configuration](reference#providing-credentials-as-configuration) in the BigQuery reference guide.

## Option 1: Using the BigQuery resource

### Step 1: Configure the BigQuery resource

To use the BigQuery resource, you'll need to add it to your `Definitions` object. The BigQuery resource requires some configuration:

- A `project`
- One method of authentication. You can follow the GCP authentication instructions [here](https://cloud.google.com/docs/authentication/provide-credentials-adc), or see [Providing credentials as configuration](reference#providing-credentials-as-configuration) in the BigQuery reference guide.

You can also specify a `location` where computation should take place.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/bigquery/tutorial/resource/configuration.py"
  startAfter="start_example"
  endBefore="end_example"
/>

### Step 2: Create tables in BigQuery

<Tabs>

<TabItem value="Create BigQuery tables in Dagster">

**Create BigQuery tables in Dagster**

Using the BigQuery resource, you can create BigQuery tables using the BigQuery Python API:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/bigquery/tutorial/resource/create_table.py"
  startAfter="start_example"
  endBefore="end_example"
/>

In this example, you're defining an asset that fetches the Iris dataset as a Pandas DataFrame and renames the columns. Then, using the BigQuery resource, the DataFrame is stored in BigQuery as the `iris.iris_data` table.

Now you can run `dagster dev` and materialize the `iris_data` asset from the Dagster UI.

</TabItem>

<TabItem value="Making Dagster aware of existing tables">

**Making Dagster aware of existing tables**

If you already have existing tables in BigQuery and other assets defined in Dagster depend on those tables, you may want Dagster to be aware of those upstream dependencies. Making Dagster aware of these tables will allow you to track the full data lineage in Dagster. You can accomplish this by defining [external assets](/guides/build/assets/external-assets) for these tables.

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/tutorial/resource/source_asset.py" />

In this example, you're creating an <PyObject section="assets" module="dagster" object="AssetSpec" /> for a pre-existing table called `iris_harvest_data`.

</TabItem>

</Tabs>

### Step 3: Define downstream assets

Once you have created an asset that represents a table in BigQuery, you will likely want to create additional assets that work with the data.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/bigquery/tutorial/resource/downstream.py"
  startAfter="start_example"
  endBefore="end_example"
/>

In this asset, you're creating second table that only contains the data for the _Iris Setosa_ species. This asset has a dependency on the `iris_data` asset. To define this dependency, you provide the `iris_data` asset as the `deps` parameter to the `iris_setosa` asset. You can then run the SQL query to create the table of _Iris Setosa_ data.

### Completed code example

When finished, your code should look like the following:

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/tutorial/resource/full_example.py" />

## Option 2: Using the BigQuery I/O manager

While using an I/O manager is not required, you may want to use an I/O manager to handle storing DataFrames as tables in BigQuery and loading BigQuery tables as DataFrames in downstream assets. You may want to use an I/O manager if:

- You want your data to be loaded in memory so that you can interact with it using Python.
- You'd like to have Dagster manage how you store the data and load it as an input in downstream assets.

{/* TODO fix link: Using an I/O manager is not required, and you can reference [When to use I/O managers](/guides/build/io-managers/#when-to-use-io-managers) to learn more. */}

This section of the guide focuses on storing and loading Pandas DataFrames in BigQuery, but Dagster also supports using PySpark DataFrames with BigQuery. The concepts from this guide apply to working with PySpark DataFrames, and you can learn more about setting up and using the BigQuery I/O manager with PySpark DataFrames in the [reference guide](/integrations/libraries/gcp/bigquery/reference).

### Step 1: Configure the BigQuery I/O manager

To use the BigQuery I/O manager, you'll need to add it to your `Definitions` object. The BigQuery I/O manager requires some configuration to connect to your Bigquery instance:

- A `project`
- One method of authentication. You can follow the GCP authentication instructions [here](https://cloud.google.com/docs/authentication/provide-credentials-adc), or see [Providing credentials as configuration](reference#providing-credentials-as-configuration) in the BigQuery reference guide.

You can also specify a `location` where data should be stored and processed and `dataset` that should hold the created tables. You can also set a `timeout` when working with Pandas DataFrames.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/bigquery/tutorial/io_manager/configuration.py"
  startAfter="start_example"
  endBefore="end_example"
/>

With this configuration, if you materialized an asset called `iris_data`, the BigQuery I/O manager would store the data in the `IRIS.IRIS_DATA` table in the `my-gcp-project` project. The BigQuery instance would be located in `us-east5`.

Finally, in the <PyObject section="definitions" module="dagster" object="Definitions" /> object, we assign the <PyObject section="libraries" module="dagster_gcp_pandas" object="BigQueryPandasIOManager" /> to the `io_manager` key. `io_manager` is a reserved key to set the default I/O manager for your assets.

For more info about each of the configuration values, refer to the <PyObject section="libraries" module="dagster_gcp_pandas" object="BigQueryPandasIOManager" /> API documentation.

### Step 2: Create tables in BigQuery \{#option-2-step-2}

The BigQuery I/O manager can create and update tables for your Dagster defined assets, but you can also make existing BigQuery tables available to Dagster.

<Tabs>

<TabItem value="Create tables in BigQuery from Dagster assets">

**Store a Dagster asset as a table in BigQuery**

To store data in BigQuery using the BigQuery I/O manager, you can simply return a Pandas DataFrame from your asset. Dagster will handle storing and loading your assets in BigQuery.

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/tutorial/io_manager/basic_example.py" />

In this example, you're defining an [asset](/guides/build/assets/defining-assets) that fetches the Iris dataset as a Pandas DataFrame, renames the columns, then returns the DataFrame. The type signature of the function tells the I/O manager what data type it is working with, so it is important to include the return type `pd.DataFrame`.

When Dagster materializes the `iris_data` asset using the configuration from [Step 1: Configure the BigQuery I/O manager](#step-1-configure-the-bigquery-io-manager), the BigQuery I/O manager will create the table `IRIS.IRIS_DATA` if it does not exist and replace the contents of the table with the value returned from the `iris_data` asset.

</TabItem>

<TabItem value="Making Dagster aware of existing tables">

**Making Dagster aware of existing tables**

If you already have existing tables in BigQuery and other assets defined in Dagster depend on those tables, you may want Dagster to be aware of those upstream dependencies. Making Dagster aware of these tables will allow you to track the full data lineage in Dagster. You can define [external assets](/guides/build/assets/external-assets) for these tables. When using an I/O manager, defining an external asset for an existing table also allows you to tell Dagster how to find the table so it can be fetched for downstream assets.

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/tutorial/io_manager/source_asset.py" />

In this example, you're creating a <PyObject section="assets" module="dagster" object="AssetSpec" /> for a pre-existing table - perhaps created by an external data ingestion tool - that contains data about iris harvests. To make the data available to other Dagster assets, you need to tell the BigQuery I/O manager how to find the data, so that the I/O manager can load the data into memory.

Because you already supplied the project and dataset in the I/O manager configuration in [Step 1: Configure the BigQuery I/O manager](#step-1-configure-the-bigquery-io-manager), you only need to provide the table name. This is done with the `key` parameter in `AssetSpec`. When the I/O manager needs to load the `iris_harvest_data` in a downstream asset, it will select the data in the `IRIS.IRIS_HARVEST_DATA` table as a Pandas DataFrame and provide it to the downstream asset.

</TabItem>
</Tabs>

### Step 3: Load BigQuery tables in downstream assets

Once you have created an asset that represents a table in BigQuery, you will likely want to create additional assets that work with the data. Dagster and the BigQuery I/O manager allow you to load the data stored in BigQuery tables into downstream assets.

<CodeExample
  path="docs_snippets/docs_snippets/integrations/bigquery/tutorial/io_manager/load_downstream.py"
  startAfter="start_example"
  endBefore="end_example"
/>

In this asset, you're providing the `iris_data` asset from the [Store a Dagster asset as a table in BigQuery](#option-2-step-2) example to the `iris_setosa` asset.

In this asset, you're providing the `iris_data` asset as a dependency to `iris_setosa`. By supplying `iris_data` as a parameter to `iris_setosa`, Dagster knows to use the `BigQueryPandasIOManager` to load this asset into memory as a Pandas DataFrame and pass it as an argument to `iris_setosa`. Next, a DataFrame that only contains the data for the _Iris Setosa_ species is created and returned. Then the `BigQueryPandasIOManager` will store the DataFrame as the `IRIS.IRIS_SETOSA` table in BigQuery.

### Completed code example

When finished, your code should look like the following:

<CodeExample path="docs_snippets/docs_snippets/integrations/bigquery/tutorial/io_manager/full_example.py" />

## Related

For more BigQuery features, refer to the [BigQuery reference](/integrations/libraries/gcp/bigquery/reference).

For more information on asset definitions, see the [Assets documentation](/guides/build/assets/).

For more information on I/O managers, see the [I/O manager documentation](/guides/build/io-managers/).
