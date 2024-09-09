---
title: "Managing stored data with I/O managers"
sidebar_position: 50
sidebar_label: "I/O managers"
---

I/O managers in Dagster provide a way to separate the code that's responsible for logical data transformation from the code that's responsible for reading and writing the results.  This can help reduce boiler plate code and make it easy to swap out where your data is stored.

<details>
<summary>Prerequisites</summary>

- Familiarity with [Assets](/concepts/assets)
- Familiarity with [Resources](/concepts/resources)
</details>

## Extract I/O logic from an asset into a reusable I/O manager

In many Dagster pipelines, assets can be broken down as the following steps:
1. reading data from some data store into memory
2. applying some in-memory transform
3. writing the transformed data to some data store

Using an I/O manager can help simplify the code responsible for reading and writing the data to and from a data source for assets that follow this pattern.

For example, both assets in the code below are constructing a DuckDB connection object, reading from an upstream table, applying some in-memory transform, and then writing the transformed result into a new table in DuckDB.

<CodeExample filePath="guides/external-systems/assets-without-io-managers.py" language="python" title="Assets without I/O managers" />

To switch to using I/O managers, we can use the DuckDB / Pandas I/O manager provided by the  `dagster_duckdb_pandas` package.  The I/O manager will be used to read and write data instead of the `DuckDBResource`.

To load an upstream asset using an I/O manager, that asset is specified as an input parameter to the asset function rather than within the `deps` list on the `@asset` decorator.  The `DuckDBPandasIOManager` reads the DuckDB table with the same name as the upstream asset and passes the data into the asset function as a Pandas DataFrame.

To store data using an I/O manager, return the data in the asset function. The data returned must be a valid type. The `DuckDBPandasIOManager` accepts Pandas data frames and writes them to DuckDB as a table with the same name as the asset.

Refer to the individual I/O manager documentation for details on valid types and how they store data.

<CodeExample filePath="guides/external-systems/assets-with-io-managers.py" language="python" title="Assets with I/O managers" />


## Swapping data stores

With I/O managers, swapping data stores consists of changing the implementation of the I/O manager resource. The asset definitions, which only contain transformational logic, won't need to change.

<CodeExample filePath="guides/external-systems/assets-with-snowflake-io-manager.py" language="python" title="Assets with Snowflake I/O manager" />

Dagster offers built-in [library implementations for I/O managers](/todo) for popular data stores and in-memory formats.
