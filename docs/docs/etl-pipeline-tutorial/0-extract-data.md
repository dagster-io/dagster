---
title: Extract data
description: Extract data with assets
sidebar_position: 10
---

In the first step in our pipeline, we will use [software-defined assets](/guides/build/assets) to load files into [DuckDB](https://duckdb.org), an analytical database. This data will serve as the foundation for the rest of the ETL tutorial.


## 1. Scaffold an asset

We will start by writing our ingestion assets. Assets serve as the building blocks for our platform in Dagster and represent the underlying entities in our pipelines (such as tables, datasets, or machine learning models).

When building assets, the first step is to scaffold the assets file with the  [`dg scaffold` command](/api/dg/dg-cli#dg-scaffold):

```bash
dg scaffold defs dagster.asset assets.py
```

This adds a file called `assets.py` that will contain our asset code to the `etl_tutorial` module:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/assets.txt" />

:::info

The `dg` CLI provides a number of commands to help structure and navigate Dagster projects. For more information, see the [`dg` CLI documentation](/api/dg/dg-cli).

:::
   
## 2. Write DuckDB helper functions

Since we will be working with DuckDB, we will need to add the DuckDB Python library to our Dagster project:

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

Now, we can think about how we want to ingest the data. For this tutorial we will be working with three files:

* [raw_customers.csv](https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv)
* [raw_orders.csv](https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv)
* [raw_payements.csv](https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv)

All of these files are located in cloud storage, and we would like to ingest each of them into a separate table in the DuckDB database. Since each file will follow a similar path into the database, we can write a function for this process:

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/assets.py"
    language="python"
    startAfter="start_import_url_to_duckdb"
    endBefore="end_import_url_to_duckdb"
    title="src/etl_tutorial/defs/assets.py"
/>

This will create a table in DuckDB from a CSV file using the `serialize_duckdb_query` function we just defined.

## 3. Define assets

Now that we have written our DuckDB helper functions, we are ready to create our assets. We will define an asset for each file we want to ingest:

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/assets.py"
    language="python"
    startAfter="start_ingest_assets_1"
    endBefore="end_ingest_assets_1"
    title="src/etl_tutorial/defs/assets.py"
/>

To ensure the <PyObject section="definitions" module="dagster" object="Definitions" /> object loads successfully, we can use the [`dg check defs`](/api/dg/dg-cli#dg-check) command:

```bash
dg check defs
```


```bash
All components validated successfully.
All definitions loaded successfully.
```


:::info

In Dagster, the <PyObject section="definitions" module="dagster" object="Definitions" /> object refers to the collection of all Dagster objects in a project. As we continue through this tutorial, we’ll add several more objects to the pipeline.

Most of these objects (such as assets) are loaded automatically via the `definitions.py` file, which was automatically generated when we first created our Dagster project:

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/definitions.py"
    language="python"
    title="src/etl_tutorial/definitions.py"
/>

:::




## 4. Materialize the assets

Now that our assets are configured, they can be viewed in the asset catalog within the Dagster UI. Navigate back to [http://127.0.0.1:3000](http://127.0.0.1:3000) (or restart `dg dev` if you have closed it) and reload the definitions:

1. Navigate to **Deployment**.
2. Click **Reload definitions**.

   ![2048 resolution](/images/tutorial/etl-tutorial/ingest-assets.png)

You should see three assets, one for each of the three raw files (customers, orders, payments) being loaded into DuckDB:

To materialize the assets:

To materialize the assets:

1. Click **Assets**, then click "View global asset lineage" to see all of your assets.
2. Click materialize all.
3. Navigate to the runs tab and select the most recent run. Here you can see the logs from the run.

   ![2048 resolution](/images/tutorial/etl-tutorial/ingest-assets-run.png)


:::tip

You can also materialize assets from the command line with [`dg` launch](/api/dg/dg-cli#dg-launch). You will need to pass an asset selection -- in this case, `*` selects all assets:

```bash
dg launch --assets "*"
```

To launch specific assets, pass an [asset selection](/guides/build/assets/asset-selection-syntax) that selects them:

```bash
dg launch --asset target/main/raw_customers,target/main/raw_orders,target/main/raw_payments
```

:::

## Summary

At this point, we have handled the ingestion layer of our ETL pipeline. The `etl_tutorial` module should look like this:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/step-0.txt" />


## Next steps

In the [next step](/etl-pipeline-tutorial/transform-data), we will build downstream assets that transform the data we have loaded into DuckDB.