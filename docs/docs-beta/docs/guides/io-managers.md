---
title: "Managing stored data with I/O managers"
sidebar_position: 50
sidebar_label: "I/O managers"
---

I/O managers in Dagster allow you to keep the code for data processing separate from the code for reading and writing data. This reduces repetitive code and makes it easier to change where your data is stored.

In many Dagster pipelines, assets can be broken down as the following steps:

1. Reading data a some data store into memory
2. Applying in-memory transform
3. Writing the transformed data to a data store

For assets that follow this pattern, an I/O manager can streamline the code that handles reading and writing data to and from a source.

<details>
<summary>Prerequisites</summary>

To follow the steps in this guide, you'll need familiarity with:

- [Assets](/concepts/assets)
- [Resources](/concepts/resources)
</details>

## Before you begin

**I/O managers aren't required to use Dagster, nor are they the best option in all scenarios.** If you find yourself writing the same code at the start and end of each asset to load and store data, an I/O manager may be useful. For example:

- You have assets that are stored in the same location and follow a consistent set of rules to determine the storage path
- You have assets that are stored differently in local, staging, and production environments
- You have assets that load upstream dependencies into memory to do the computation

**I/O managers may not be the best fit if:**

- You want to run SQL queries that create or update a table in a database
- Your pipeline manages I/O on its own by using other libraries/tools that write to storage
- Your assets won't fit in memory, such as a database table with billions of rows

As a general rule, if your pipeline becomes more complicated in order to use I/O managers, it's likely that I/O managers aren't a good fit. In these cases you should use `deps` to [define dependencies](/guides/asset-dependencies).

## Using I/O managers in assets \{#io-in-assets}

Consider the following example, which contains assets that construct a DuckDB connection object, read data from an upstream table, apply some in-memory transform, and write the result to a new table in DuckDB:

<CodeExample filePath="guides/external-systems/assets-without-io-managers.py" language="python" />

Using an I/O manager would remove the code that reads and writes data from the assets themselves, instead delegating it to the I/O manager. The assets would be left only with the code that applies transformations or retrieves the initial CSV file.

<CodeExample filePath="guides/external-systems/assets-with-io-managers.py" language="python" />

To load upstream assets using an I/O manager, specify the asset as an input parameter to the asset function. In this example, the `DuckDBPandasIOManager` I/O manager will read the DuckDB table with the same name as the upstream asset (`raw_sales_data`) and pass the data to `clean_sales_data` as a Pandas DataFrame.

To store data using an I/O manager, return the data in the asset function. The returned data must be a valid type. This example uses Pandas DataFrames, which the `DuckDBPandasIOManager` will write to a DuckDB table with the same name as the asset.

Refer to the individual I/O manager documentation for details on valid types and how they store data.

## Swapping data stores \{#swap-data-stores}

With I/O managers, swapping data stores consists of changing the implementation of the I/O manager. The asset definitions, which only contain transformational logic, won't need to change.

In the following example, a Snowflake I/O manager replaced the DuckDB I/O manager.

<CodeExample filePath="guides/external-systems/assets-with-snowflake-io-manager.py" language="python" />

## Built-in I/O managers \{#built-in}

Dagster offers built-in library implementations for I/O managers for popular data stores and in-memory formats.

| Name                                                                                       | Description                                                                   |
| ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| <PyObject module="dagster" object="FilesystemIOManager" />                                 | Default I/O manager. Stores outputs as pickle files on the local file system. |
| <PyObject module="dagster" object="InMemoryIOManager" />                                   | Stores outputs in memory. Primarily useful for unit testing.                  |
| <PyObject module="dagster_aws.s3" object="S3PickleIOManager" />                            | Stores outputs as pickle files in Amazon Web Services S3.                     |
| <PyObject module="dagster_azure.adls2" object="ConfigurablePickledObjectADLS2IOManager" /> | Stores outputs as pickle files in Azure ADLS2.                                |
| <PyObject module="dagster_gcp" object="GCSPickleIOManager" />                              | Stores outputs as pickle files in Google Cloud Platform GCS.                  |
| <PyObject module="dagster_gcp_pandas" object="BigQueryPandasIOManager" />                  | Stores Pandas DataFrame outputs in Google Cloud Platform BigQuery.            |
| <PyObject module="dagster_gcp_pyspark" object="BigQueryPySparkIOManager" />                | Stores PySpark DataFrame outputs in Google Cloud Platform BigQuery.           |
| <PyObject module="dagster_snowflake_pandas" object="SnowflakePandasIOManager" />           | Stores Pandas DataFrame outputs in Snowflake.                                 |
| <PyObject module="dagster_snowflake_pyspark" object="SnowflakePySparkIOManager" />         | Stores PySpark DataFrame outputs in Snowflake.                                |
| <PyObject module="dagster_duckdb_pandas" object="DuckDBPandasIOManager" />                 | Stores Pandas DataFrame outputs in DuckDB.                                    |
| <PyObject module="dagster_duckdb_pyspark" object="DuckDBPySparkIOManager" />               | Stores PySpark DataFrame outputs in DuckDB.                                   |
| <PyObject module="dagster_duckdb_polars" object="DuckDBPolarsIOManager" />                 | Stores Polars DataFrame outputs in DuckDB.                                    |                                       |

## Next steps

- Learn to [connect databases](/guides/databases) with resources
- Learn to [connect APIs](/guides/apis) with resources