---
title: Extract data
description: Extract data with assets
sidebar_position: 10
---

In the first step in our pipeline, we will use [software-defined assets](/guides/build/assets) to load files into [DuckDB](https://duckdb.org), an analytical database. This data will serve as the foundation for the rest of the ETL tutorial.

## 1. Scaffold an asset

We will start by writing our ingestion assets. Assets serve as the building blocks for our platform in Dagster and represent the underlying entities in our pipelines (such as tables, datasets, or machine learning models). Assets take dependencies on other assets to build out the full graph of our data platform and define its lineage.

When building assets, the first step is to scaffold the assets file with the [`dg scaffold` command](/api/clis/dg-cli/dg-cli-reference#dg-scaffold). The `dg` CLI provides a number of commands to help structure and navigate Dagster projects. For more information, see the [`dg` CLI documentation](/api/clis/dg-cli/dg-cli-reference):

<CliInvocationExample path="docs_projects/project_etl_tutorial/commands/dg-scaffold-assets.txt" />

This adds a file called `assets.py` that will contain our asset code to the `etl_tutorial` module. Using `dg` to create the file ensures that the file is in a location where it can be automatically discovered by Dagster:

<CliInvocationExample path="docs_projects/project_etl_tutorial/tree/assets.txt" />

## 2. Write DuckDB helper functions

Since we will be working with DuckDB, we will need to add the DuckDB Python library to our Dagster project:

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      Install the required dependencies:

         ```shell
         uv add duckdb
         ```

   </TabItem>

   <TabItem value="pip" label="pip">
      Install the required dependencies:

         ```shell
         pip install duckdb
         ```

   </TabItem>
</Tabs>

We can use this library to establish a connection with a DuckDB database running locally. We will define multiple assets using the same DuckDB database, so we will want to write a helper function to ensure that each asset can acquire a lock on the DuckDB database file when writing data:

<CodeExample
  path="docs_projects/project_etl_tutorial/src/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_serial_execute"
  endBefore="end_serial_execute"
  title="src/etl_tutorial/defs/assets.py"
/>

This function ensures that the query holds a lock on the file throughout its execution. Now, we can think about how we want to ingest the data into DuckDB. For this tutorial we will be working with three files:

- [raw_customers.csv](https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv)
- [raw_orders.csv](https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv)
- [raw_payements.csv](https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv)

All of these files are located in cloud storage, and we would like to ingest each of them into a separate table in the DuckDB database. In Dagster, we want each table to be represented as its own asset. Because each asset will have similar logic for ingesting the files, we can write a function to standardize the logic:

<CodeExample
  path="docs_projects/project_etl_tutorial/src/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_import_url_to_duckdb"
  endBefore="end_import_url_to_duckdb"
  title="src/etl_tutorial/defs/assets.py"
/>

This function will take in the URL for one of our files and a table name, and load the data into DuckDB using [DuckDB CSV import](https://duckdb.org/docs/stable/data/csv/overview.html) functionality. Then using the `serialize_duckdb_query` function we just defined, it will execute the query while ensuring a proper lock on the DuckDB database.

## 3. Define assets

Now that we have written our DuckDB helper functions, we are ready to create our assets. We will define an asset for each file we want to ingest:

<CodeExample
  path="docs_projects/project_etl_tutorial/src/etl_tutorial/defs/assets.py"
  language="python"
  startAfter="start_ingest_assets_1"
  endBefore="end_ingest_assets_1"
  title="src/etl_tutorial/defs/assets.py"
/>

In Dagster, an asset is defined by the <PyObject section="assets" module="dagster" object="asset" decorator />. Any function with that decorator will be treated as part of the Dagster asset graph. Within that decorator, we can define some optional characteristics of the asset itself:

- The `kinds` argument adds metadata about the tools and technologies used by the asset.
- The `key` argument defines the key path of the asset. Without setting the key argument, the asset key will be the function name. Here we will explicitly set a key for our assets to work with our dbt project in the next step.

## 4. Dagster definitions

In Dagster, all the objects we define (such as assets) need to be associated with a top-level <PyObject section="definitions" module="dagster" object="Definitions" /> object in order to be deployed. When we first created our project with `uvx create-dagster project`, a `definitions.py` file was created as well:

<CodeExample
  path="docs_projects/project_etl_tutorial/src/etl_tutorial/definitions.py"
  language="python"
  title="src/etl_tutorial/definitions.py"
/>

This `Definitions` object loads the `etl_tutorial` module and automatically discovers all the assets and other Dagster objects we define. There is no need to explicitly include any references to assets as they are created. However, it is a good practice to check that the `Definitions` object can be loaded without error as we add Dagster objects.

We can use `dg` to ensure that everything we define in our module is loading correctly and that our project is deployable. Here we can use the [`dg check defs`](/api/clis/dg-cli/dg-cli-reference#dg-check) command:

<CliInvocationExample path="docs_projects/project_etl_tutorial/commands/dg-check-defs.txt" />

This tells us there are no issues with any of the assets we have defined. As you develop your Dagster project, it is a good habit to run `dg check` to ensure everything is working as expected.

## 5. Materialize the assets

Now that our assets are configured and we have verified that the top-level `Definitions` object is valid, we can view the asset catalog within the Dagster UI. Navigate back to [http://127.0.0.1:3000](http://127.0.0.1:3000) (or restart `dg dev` if you have closed it) and reload the definitions:

1. Navigate to **Deployment**.
2. Click **Reload definitions**.

   ![2048 resolution](/images/tutorial/etl-tutorial/ingest-assets.png)

You should see three assets, one for each of the three raw files (customers, orders, payments) being loaded into DuckDB:

To materialize the assets:

1. Click **Assets**, then click "View global asset lineage" to see all of your assets.
2. Click materialize all.
3. Navigate to the runs tab and select the most recent run. Here you can see the logs from the run.

   ![2048 resolution](/images/tutorial/etl-tutorial/ingest-assets-run.png)

:::tip

You can also materialize assets from the command line with [`dg` launch](/api/clis/dg-cli/dg-cli-reference#dg-launch). You will need to pass an asset selection -- in this case, `*` selects all assets:

<CliInvocationExample contents='dg launch --assets "*"' />

To launch specific assets, pass an [asset selection](/guides/build/assets/asset-selection-syntax) that selects them:

<CliInvocationExample contents="dg launch --asset target/main/raw_customers,target/main/raw_orders,target/main/raw_payments" />

:::

## Summary

At this point, we have handled the ingestion layer of our ETL pipeline. The `etl_tutorial` module should look like this:

<CliInvocationExample path="docs_projects/project_etl_tutorial/tree/step-0.txt" />

There are three assets which each load a file into DuckDB. We have also seen how assets are automatically loaded into the `definitions` object that holds all of the objects in our project.

## Next steps

In the [next step](/examples/full-pipelines/etl-pipeline/transform-data), we will build downstream assets that transform the data we have loaded into DuckDB.
