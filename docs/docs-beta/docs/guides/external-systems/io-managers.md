---
title: "Managing stored data with I/O Managers"
sidebar_position: 50
sidebar_label: "Storing data with I/O Managers"
---

IO Managers in Dagster provide a way to separate the code that's responsible for logical data transformation from the code that's responsible for reading and writing the results.  This can help reduce boiler plate code and make it easy to swap out where your data is stored.

<details>
<summary>Prerequisites</summary>

- Familiarity with [Assets](/concepts/assets)
- Familiarity with [Ops and Jobs](/concepts/ops-jobs)
- Familiarity with [Resources](/concepts/resources)
</details>

## Extract IO logic from an asset into a reuseable IO Manager

In many dagster jobs, assets can be broken down as the following steps:
1. reading data from some data store into memory
2. applying some in-memory transform
3. writing the transformed data to some data store

For assets that follow this pattern, using an IO manager can help remove the boiler-plate of the code responsible for reading and writing the data to and from a data source.

For example, both assets in the code below are constructing a Snowflake connection object, reading from an upstream table, applying some in-memory transform, and then uploading the transformed result into a new table in Snowflake.

<CodeExample filePath="guides/external-systems/assets-without-io-managers.py" language="python" title="Assets without IO managers" />

To switch to using IO managers, we can use the `dagster_snowflake` package's Snowflake / Pandas IO manager instead of the `SnowflakeResource`.  The IO manager reads upstream assets  from the Snowflake table with the shared name.  These are passed into the asset function as Pandas dataframes.  The return type of the asset function should be the transformed Pandas dataframe.  The IO manager is responsible for uploading that dataframe to Snowflake into a table matching the asset definition's name.

<CodeExample filePath="guides/external-systems/assets-with-io-managers.py" language="python" title="Asset with IO managers" />
