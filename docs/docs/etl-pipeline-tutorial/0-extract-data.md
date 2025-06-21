---
title: Extract data
description: Extract data with Sling
sidebar_position: 10
---

In the first step of the tutorial, you will use [Sling](https://slingdata.io/), an ETL framework, to load files into [DuckDB](https://duckdb.org/), an analytical database. This data will serve as the foundation for the rest of the ETL tutorial. In this step, you will:

- Integrate with Sling
- Build software-defined assets from a Sling project using Dagster components
   
## 1. Define the Sling Component

To begin you will need to install Dagster's Sling integration into the Dagster project:

```bash
uv pip install dagster-sling
```

This will install the Dagster library for Sling. Using `dg` this library also provides access to the Sling component. In order to view the Sling component, run `dg list`:

```bash
dg list components
```

The standard Dagster library supports several components, but after adding `dagster-sling` you will see a new entry for Sling:
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Key                                               ┃ Summary                                                     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┃
│ dagster_sling.SlingReplicationCollectionComponent │ Expose one or more Sling replications to Dagster as assets. │
└───────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────┘
```

We can now scaffold the Sling component using `dg`:

```bash
dg scaffold defs 'dagster_sling.SlingReplicationCollectionComponent' ingest
```

This adds a Sling component, `ingest`, to the `etl_tutorial` module:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/sling.txt" />

These are all the files necessary to integrate Sling with Dagster. Next we can customize the Sling component to pull in our target data and map it to the correct destinations.

## 2. Configure the Sling `replication.yaml`

For this tutorial we will be working with three files.

* [raw_customers.csv](https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_customers.csv)
* [raw_orders.csv](https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_orders.csv)
* [raw_payements.csv](https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/refs/heads/main/seeds/raw_payments.csv)

All of these files are located in the cloud storage and we would like to ingest each of them into a separate table in the DuckDB database.

Sling manages these configurations with the `replication.yaml`. This file is specific to Sling and is one of the files added when we scaffolded the Sling component with `dg`. Update the `replication.yaml` file to the following:

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/ingest/replication.yaml"
    language="yaml"
    title="src/etl_tutorial/defs/ingest/replication.yaml"
/>

This defines what files are being pulled in and the destination. The important part to understand are the `streams` which map the files to specific tables.

## 3. Configure the Sling `defs.yaml`

The other configuration that needs to be set is in the `defs.yaml`. This is the Dagster specific file that defines the `SlingReplicationCollectionComponent` component. Here we will set the destination as DuckDB database details. We will also set the path to the `replication.yaml` that we defined previously.

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/ingest/defs.yaml"
    language="yaml"
    title="src/etl_tutorial/defs/ingest/defs.yaml"
/>

That is everything necessary for the component. To ensure everything is configured correctly you can use `dg check` in the command line:

```bash
dg check defs
```

This will confirm that the Dagster Definition can load successfully and will show if there are any errors in the project.

## 4. Executing the assets

Now that the Sling component has been configured you can view the asset catalog within the Dagster UI. Navigate back to [http://127.0.0.1:3000](http://127.0.0.1:3000) (or restart `dg dev` if you have closed it) and reload the definition:

1. Navigate to **Deployment**.
2. Click Reload definitions.

TODO: Screenshot

You will see six assets. Each of the three files (customers, orders, payments) is represented by a pair of assets, one representing the file in cloud storage and one for the file as table within DuckDB with Sling. You can launch these assets in the UI:

1. Click **Assets**, then click "View global asset lineage" to see all of your assets.
2. Click materialize all.
3. Navigate to the runs tab and select the most recent run. Here you can see the logs from the run.

You can also launch those assets via the command line by using `dg`:

```bash
dg launch --assets *
```

You can also launch specific assets by [selecting their asset keys](/guides/build/assets/asset-selection-syntax/):

```bash
dg launch --assets target/main/raw_customers,target/main/raw_orders,target/main/raw_payments
```

:::info

TODO: Relationship between components and definitions

:::

## Summary

We have already handled the ingestion layer of our ETL pipeline. The `etl_tutorial` module should look like this:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/step-0.txt" />

You have seen how to use `dg` and components to quickly spin up Dagster assets and how to launch assets through the UI and command line.

## Next steps

- Continue this tutorial with your [transform data](/etl-pipeline-tutorial/transform-data)
