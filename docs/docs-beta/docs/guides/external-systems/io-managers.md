---
title: "Managing stored data with I/O Managers"
sidebar_position: 50
sidebar_label: "Storing data with I/O Managers"
---

I/O Managers in Dagster provide a way to separate the code that's responsible for logical data transformation from the code that's responsible for reading and writing the results.  This can help reduce boiler plate code and make it easy to swap out where your data is stored.

<details>
<summary>Prerequisites</summary>

- Familiarity with [Assets](/concepts/assets)
- Familiarity with [Resources](/concepts/resources)
</details>

## Extract I/O logic from an asset into a reuseable I/O Manager

In many Dagster pipelines, assets can be broken down as the following steps:
1. reading data from some data store into memory
2. applying some in-memory transform
3. writing the transformed data to some data store

For assets that follow this pattern, using an I/O manager can help remove the boiler-plate of the code responsible for reading and writing the data to and from a data source.

For example, both assets in the code below are constructing a DuckDB connection object, reading from an upstream table, applying some in-memory transform, and then writing the transformed result into a new table in DuckDB.

<CodeExample filePath="guides/external-systems/assets-without-io-managers.py" language="python" title="Assets without I/O managers" />

To switch to using I/O managers, we can use the DuckDB / Pandas I/O manager provided by the  `dagster_duckdb_pandas` package.  The I/O manager will be used to read and write data instead of the `DuckDBResource`.

To load an upstream asset using an I/O manager, that asset is specified as an input parameter to the asset function rather than within the `deps` list on the `@asset` decorator.  The `DuckDBPandasIOManager` specifically reads the DuckDB table with the same name as the upstream asset and passes the data into the asset function as a Pandas dataframe. 

To store data using an I/O manager, the data should be returned by the asset function.  The `DuckDBPandasIOManager` specifically takes the returned value from the asset function, which should be a Pandas dataframe, and writes it to the DuckDB file as a table with the same name as the asset.

<CodeExample filePath="guides/external-systems/assets-with-io-managers.py" language="python" title="Asset with I/O managers" />


## Swapping data stores

With I/O managers, swapping data stores consists of changing the implementation of the I/O manager resource.  The asset definitions (which should now only contain transformational logic) should not change.

<CodeExample filePath="guides/external-systems/assets-with-snowflake-io-manager.py" language="python" title="Asset with Snowflake I/O manager" />

Dagster offers a number of [library implementations for I/O managers] - TODO ADD LINK.

