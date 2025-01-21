---
title: "Define assets upstream of your dbt models"
description: Dagster can orchestrate dbt alongside other technologies.
sidebar_position: 300
---

By this point, you've [set up a dbt project](set-up-dbt-project) and [loaded dbt models into Dagster as assets](load-dbt-models).

However, the tables at the root of the pipeline are static: they're [dbt seeds](https://docs.getdbt.com/docs/build/seeds), CSVs that are hardcoded into the dbt project. In a more realistic data pipeline, these tables would typically be ingested from some external data source, for example by using a tool like Airbyte or Fivetran, or by Python code.

These ingestion steps in the pipeline often don't make sense to define inside dbt, but they often still do make sense to define as Dagster assets. You can think of a Dagster asset definition as a more general version of a dbt model. A dbt model is one kind of asset, but another kind is one that's defined in Python, using Dagster's Python API. The dbt integration reference page includes a [section](/integrations/libraries/dbt/reference#dbt-models-and-dagster-asset-definitions) that outlines the parallels between dbt models and Dagster asset definitions.

In this section, you'll replace the `raw_customers` dbt seed with a Dagster asset that represents it. You'll write Python code that populates this table by fetching data from the web. This will allow you to launch runs that first execute Python code to populate the `raw_customers` table and then invoke dbt to populate the downstream tables.

You'll:

- [Install the Pandas and DuckDB Python libraries](#step-1-install-the-pandas-and-duckdb-python-libraries)
- [Define an upstream Dagster asset](#step-2-define-an-upstream-dagster-asset)
- [In the dbt project, replace a seed with a source](#step-3-in-the-dbt-project-replace-a-seed-with-a-source)
- [Materialize the assets using the Dagster UI](#step-4-materialize-the-assets-using-the-dagster-ui)

## Step 1: Install the Pandas and DuckDB Python libraries

The Dagster asset that you write will fetch data using [Pandas](https://pandas.pydata.org/) and write it out to your DuckDB warehouse using [DuckDB's Python API](https://duckdb.org/docs/api/python/overview.html). To use these, you'll need to install them:

```shell
pip install pandas duckdb pyarrow
```

## Step 2: Define an upstream Dagster asset

To fetch the data the dbt models require, we'll write a Dagster asset for `raw_customers`. We'll put this asset in our `assets.py` file, inside the `jaffle_dagster` directory. This is the file that contains the code that defines our dbt models, which we reviewed at the end of the [last section](load-dbt-models#step-4-understand-the-python-code-in-your-dagster-project). Copy and paste this code to overwrite the existing contents of that file:

<CodeExample path="docs_snippets/docs_snippets/integrations/dbt/tutorial/upstream_assets/assets.py" startAfter="start_python_assets" endBefore="end_python_assets" />

Let's review the changes we made:

1. At the top, we added imports for `pandas` and `duckdb`, which we use for fetching data into a `DataFrame` and writing it to DuckDB.

2. We added a `duckdb_database_path` variable, which holds the location of our DuckDB database. Remember that DuckDB databases are just regular files on the local filesystem. The path is the same path that we used when we configured our `profiles.yml` file. This variable is used in the implementations of the `raw_customers` asset.

3. We added a definition for the `raw_customers` table by writing a function named `raw_customers` and decorating it with the <PyObject section="assets" module="dagster" object="asset" decorator /> decorator. We labeled it with `compute_kind="python"` to indicate in the Dagster UI that this is an asset defined in Python. The implementation inside the function fetches data from the internet and writes it to a table in our DuckDB database. Similar to how running a dbt model executes a select statement, materializing this asset will execute this Python code.

Finally, let's update the `assets` argument of our `Definitions` object, in `definitions.py`, to include the new asset we just defined:

<CodeExample path="docs_snippets/docs_snippets/integrations/dbt/tutorial/upstream_assets/definitions.py" startAfter="start_defs" endBefore="end_defs" />

## Step 3: In the dbt project, replace a seed with a source

1. Because we're replacing it with a Dagster asset, we no longer need the dbt seed for `raw_customers`, so we can delete it:

   ```shell
   cd ..
   rm seeds/raw_customers.csv
   ```

2. Instead, we want to tell dbt that `raw_customers` is a table that is defined outside of the dbt project. We can do that by defining it inside a [dbt source](https://docs.getdbt.com/docs/build/sources).

   Create a file called `sources.yml` inside the `models/` directory, and put this inside it:

   ```yaml
   version: 2

   sources:
     - name: jaffle_shop
       tables:
         - name: raw_customers
           meta:
             dagster:
               asset_key: ["raw_customers"] # This metadata specifies the corresponding Dagster asset for this dbt source.
   ```

This is a standard dbt source definition, with one addition: it includes metadata, under the `meta` property, that specifies the Dagster asset that it corresponds to. When Dagster reads the contents of the dbt project, it reads this metadata and infers the correspondence. For any dbt model that depends on this dbt source, Dagster then knows that the Dagster asset corresponding to the dbt model should depend on the Dagster asset corresponding to the source.

3. Then, update the model that depends on the `raw_customers` seed to instead depend on the source. Replace the contents of `model/staging/stg_customers.sql` with this:

   ```sql
   with source as (

       {#-
       Use source instead of seed:
       #}
       select * from {{ source('jaffle_shop', 'raw_customers') }}

   ),

   renamed as (

       select
           id as customer_id,
           first_name,
           last_name

       from source

   )

   select * from renamed
   ```

## Step 4: Materialize the assets using the Dagster UI

If the Dagster UI is still running from the previous section, click the "Reload Definitions" button in the upper right corner. If you shut it down, then you can launch it again with the same command from the previous section:

```shell
dagster dev
```

Our `raw_customers` model is now defined as a Python asset. We can also see that assets downstream of this new Python asset, such as `stg_customers` and `customers`, are now marked stale because the code definition of `raw_customers` has changed.

![Asset group with dbt models and Python asset](/images/integrations/dbt/using-dbt-with-dagster/upstream-assets/asset-graph.png)

Click the **Materialize all** button. This will launch a run with two steps:

- Run the `raw_customers` Python function to fetch data and write the `raw_customers` table to DuckDB.
- Run all the dbt models using `dbt build`, like in the last section.

If you click to view the run, you can see a graphical representation of these steps, along with logs.

![Run page for run with dbt models and Python asset](/images/integrations/dbt/using-dbt-with-dagster/upstream-assets/run-page.png)


## What's next?

At this point, you've built and materialized an upstream Dagster asset, providing source data to your dbt models. In the last section of the tutorial, we'll show you how to add a [downstream asset to the pipeline](downstream-assets).
