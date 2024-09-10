---
title: Pass data between assets
description: Learn how to pass data between assets in Dagster
sidebar_position: 30
last_update:
  date: 2024-08-11
  author: Pedram Navid
---

In Dagster, assets are the building blocks of your data pipeline and it's common to want to pass data between them. This guide will help you understand how to pass data between assets.

There are three ways of passing data between assets:

- Explicitly managing data, by using external storage
- Implicitly managing data, using I/O managers
- Avoiding passing data between assets altogether by combining several tasks into a single asset

This guide walks through all three methods.

---

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- A basic understanding of Dagster concepts such as assets and resources
- Dagster and the `dagster-duckdb-pandas` package installed
</details>

---

## Move data assets explicitly using external storage

A common and recommended approach to passing data between assets is explicitly managing data using external storage. This example pipeline uses a SQLite database as external storage:

<CodeExample filePath="guides/data-assets/passing-data-assets/passing-data-explicit.py" language="python" title="Using External Storage" />

In this example, the first asset opens a connection to the SQLite database and writes data to it. The second asset opens a connection to the same database and reads data from it. The dependency between the first asset and the second asset is made explicit through the asset's `deps` argument.

The benefits of this approach are:

- It's explicit and easy to understand how data is stored and retrieved
- You have maximum flexibility in terms of how and where data is stored, for example, based on environment

The downsides of this approach are:

- You need to manage connections and transactions manually
- You need to handle errors and edge cases, for example, if the database is down or if a connection is closed

## Move data between assets implicitly using I/O managers

Dagster's I/O managers are a powerful feature that manages data between assets by defining how data is read from and written to external storage. They help separate business logic from I/O operations, reducing boilerplate code and making it easier to change where data is stored.

I/O managers handle:

1. **Input**: Reading data from storage and loading it into memory for use by dependent assets.
2. **Output**: Writing data to the configured storage location.

For a deeper understanding of I/O managers, check out the [Understanding I/O managers](/concepts/io-managers) guide.

<CodeExample filePath="guides/data-assets/passing-data-assets/passing-data-io-manager.py" language="python" title="Using I/O managers" />

In this example, a `DuckDBPandasIOManager` is instantiated to run using a local file. The I/O manager handles both reading and writing to the database.

:::warning

This example works for local development, but in a production environment
each step would execute in a separate environment and would not have access to the same file system. Consider a cloud-hosted environment for production purposes.

:::

The `people()` and `birds()` assets both write their dataframes to DuckDB
for persistent storage. The `combined_data()` asset requests data from both assets by adding them as parameters to the function, and the I/O manager handles the reading them from DuckDB and making them available to the `combined_data` function as dataframes. **Note**: When you use I/O managers you don't need to manually add the asset's dependencies through the `deps` argument.

The benefits of this approach are:

- The reading and writing of data is handled by the I/O manager, reducing boilerplate code
- It's easy to swap out different I/O managers based on environments without changing the underlying asset computation

The downsides of this approach are:

- The I/O manager approach is less flexible should you need to customize how data is read or written to storage
- Some decisions may be made by the I/O manager for you, such as naming conventions that can be hard to override.

## Avoid passing data between assets by combining assets

In some cases, you may find that you can avoid passing data between assets by
carefully considering how you have modeled your pipeline:

Consider this example:

<CodeExample filePath="guides/data-assets/passing-data-assets/passing-data-avoid.py" language="python" title="Avoid Passing Data Between Assets" />

This example downloads a zip file from Google Drive, unzips it, and loads the data into a Pandas DataFrame. It relies on each asset running on the same file system to perform these operations.

The assets are modeled as tasks, rather than as data assets. For more information on the difference between tasks and data assets, check out the [Thinking in Assets](/concepts/assets/thinking-in-assets) guide.

In this refactor, the `download_files`, `unzip_files`, and `load_data` assets are combined into a single asset, `my_dataset`. This asset downloads the files, unzips them, and loads the data into a data warehouse.

<CodeExample filePath="guides/data-assets/passing-data-assets/passing-data-rewrite-assets.py" language="python" title="Avoid Passing Data Between Assets" />

This approach still handles passing data explicitly, but no longer does it across assets,
instead within a single asset. This pipeline still assumes enough disk and
memory available to handle the data, but for smaller datasets, it can work well.

The benefits of this approach are:

- All the computation that defines how an asset is created is contained within a single asset, making it easier to understand and maintain
- It can be faster than relying on external storage, and doesn't require the overhead of setting up additional compute instances.

The downsides of this approach are:

- It makes certain assumptions about how much data is being processed
- It can be difficult to reuse functions across assets, since they're tightly coupled to the data they produce
- It may not always be possible to swap functionality based on the environment you are running in. For example, if you are running in a cloud environment, you may not have access to the local file system.

---

## Related resources

{/* TODO: add links to relevant API documentation here. */}
