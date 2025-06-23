---
title: Extract data
description: Extract data with assets
sidebar_position: 10
---

The first step in our pipeline will be loading files into [DuckDB](https://duckdb.org/), an analytical database. This data will serve as the foundation for the rest of the ETL tutorial. In this step, you will:

- Build software-defined assets

## 1. Scaffold an asset

We will start by writing our ingestion [assets](/guides/build/assets). Assets serve as the building blocks for our platform in Dagster and represent the underlying entities in our pipelines (such as database tables, machine learning models...).

When building assets, the first step is to scaffold the assets file with the Dagster CLI [`dg`](/api/dg/dg-cli). This provides a number of commands that can help structure and navigate a Dagster project. We will use [`dg scaffold`](/api/dg/dg-cli#dg-scaffold) to include assets:

```bash
dg scaffold defs dagster.asset assets.py
```

This adds a file, `assets.py`, to the `etl_tutorial` module:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/assets.txt" />

This is where our asset code will go.
   
## 2. Working with DuckDB

Since we will be working with DuckDB we want to add the DuckDB Python library to our Dagster project:

```bash
uv pip install duckdb
```

Next, we need to write a helper function for working with DuckDB. Since we’ll be ingesting multiple files, it’s important to ensure that each asset can acquire a lock on the DuckDB database file. This function ensures that the query holds a lock on the file throughout its execution:

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/assets.py"
    language="python"
    startAfter="start_serial_execute"
    endBefore="end_serial_execute"
    title="src/etl_tutorial/defs/assets.py"
/>

Now we can think about how we want to ingest the data. For this tutorial we will be working with three files.

* [raw_customers.csv](https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv)
* [raw_orders.csv](https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv)
* [raw_payements.csv](https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv)

All of these files are located in the cloud storage and we would like to ingest each of them into a separate table in the DuckDB database. Since each file will follow a similar path into the database, we can write a function for this process:

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/assets.py"
    language="python"
    startAfter="start_import_url_to_duckdb"
    endBefore="end_import_url_to_duckdb"
    title="src/etl_tutorial/defs/assets.py"
/>

This will create a table in DuckDB from the CSV file using the `serialize_duckdb_query` we just defined.

## 3. Defining assets

With all of that done, we are ready to create our assets. We will define an asset for each file we want to ingest:

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/assets.py"
    language="python"
    startAfter="start_ingest_assets_1"
    endBefore="end_ingest_assets_1"
    title="src/etl_tutorial/defs/assets.py"
/>

To ensure everything is configured correctly you can use [`dg check`](/api/dg/dg-cli#dg-check) in the command line:

```bash
dg check defs
```

This step confirms that the Dagster `definition` can load successfully and helps identify any errors in the project.

```bash
All components validated successfully.
All definitions loaded successfully.
```

In Dagster, the `definition` refers to the collection of all Dagster objects that make up your project. As we continue through this tutorial, we’ll add several more objects to the pipeline.

Most of these objects (such as assets) are loaded automatically via the definitions.py file:

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/definitions.py"
    language="python"
    title="src/etl_tutorial/definitions.py"
/>

This file was automatically generated when we first created the Dagster project using `uvx create-dagster project`, and it loads our `etl_tutorial` module where our assets are located.

## 4. Executing the assets

Now that our assets are configured, you can view the asset catalog within the Dagster UI. Navigate back to [http://127.0.0.1:3000](http://127.0.0.1:3000) (or restart `dg dev` if you have closed it) and reload the definition:

1. Navigate to **Deployment**.
2. Click Reload definitions.

   ![2048 resolution](/images/tutorial/etl-tutorial/ingest-assets.png)

You will see three assets one for each our the three raw files (customers, orders, payments) that we are loading into DuckDB:

1. Click **Assets**, then click "View global asset lineage" to see all of your assets.
2. Click materialize all.
3. Navigate to the runs tab and select the most recent run. Here you can see the logs from the run.

   ![2048 resolution](/images/tutorial/etl-tutorial/ingest-assets-run.png)

You can also launch those assets via the command line by using [`dg launch`](/api/dg/dg-cli#dg-launch):

```bash
dg launch --assets "*"
```

You can also launch specific assets by [selecting their asset keys](/guides/build/assets/asset-selection-syntax/):

```bash
dg launch --assets target/main/raw_customers,target/main/raw_orders,target/main/raw_payments
```

## Summary

We have already handled the ingestion layer of our ETL pipeline. The `etl_tutorial` module should look like this:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/step-0.txt" />

Next we will build out downstream assets that use the data we have brought into DuckDB.

## Next steps

- Continue this tutorial with your [transform data](/etl-pipeline-tutorial/transform-data)
