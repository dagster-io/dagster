---
layout: Integration
status: published
name: Sling
title: Dagster & Sling
sidebar_label: Sling
excerpt: Extract and load data from popular data sources to destinations with Sling through Dagster.
date: 2024-08-30
apireflink: https://docs.dagster.io/api/python-api/libraries/dagster-sling
docslink: https://docs.dagster.io/integrations/libraries/sling
partnerlink: https://slingdata.io/
categories:
  - ETL
enabledBy:
enables:
tags: [dagster-supported, etl]
sidebar_custom_props:
  logo: images/integrations/sling.png
---

Sling provides an easy-to-use YAML configuration layer for loading data from files, replicating data between databases, exporting custom SQL queries to cloud storage, and much more.

---

## How it works

The Dagster integration allows you to derive Dagster assets from a replication configuration file. The typical pattern for building an ELT pipeline with Sling has three steps:

1. Define a Sling [`replication.yaml`](https://docs.slingdata.io/sling-cli/run/configuration/replication) file that specifies the source and target connections, as well as which streams to sync from.

2. Create a <PyObject section="libraries" module="dagster_sling" object="SlingResource" /> and pass a list of <PyObject section="libraries" module="dagster_sling" object="SlingConnectionResource" /> for each connection to the `connection` parameter, ensuring the resource uses the same name given to the connection in the Sling configuration.

3. Use the <PyObject section="libraries" module="dagster_sling" object="sling_assets" decorator /> decorator to define an asset that runs the Sling replication job and yields from the <PyObject section="libraries" module="dagster_sling" object="SlingResource" method="replicate" /> method to run the sync.

We'll walk you through each of these steps in this guide.

---

## Prerequisites

To follow the steps in this guide:

- **Familiarize yourself with [Sling's replication configuration](https://docs.slingdata.io/sling-cli/run/configuration/replication)**, if you've never worked with Sling before. The replication configuration is a YAML file that specifies the source and target connections, as well as which streams to sync from. The `dagster-sling` integration uses this configuration to build assets for both sources and destinations.
- **To install the following libraries**:

  ```bash
  pip install dagster dagster-sling
  ```

  Refer to the [Dagster installation](/getting-started/installation) guide for more info.

---

## Step 1: Set up a Sling replication configuration

Dagster's Sling integration is built around Sling's replication configuration. You may provide either a path to an existing `replication.yaml` file or construct a dictionary that represents the configuration in Python. This configuration is passed to the Sling CLI to run the replication job.

<Tabs>
<TabItem value="replication.yaml">

### replication.yaml

This example creates a replication configuration in a `replication.yaml` file:

```yaml
# replication.yaml

source: MY_POSTGRES
target: MY_SNOWFLAKE

defaults:
  mode: full-refresh
  object: "{stream_schema}_{stream_table}"

streams:
  public.accounts:
  public.users:
  public.finance_departments:
    object: "departments"
```

</TabItem>
<TabItem value="Python">

### Python

This example creates a replication configuration using Python:

<CodeExample path="docs_snippets/docs_snippets/integrations/sling/replication_config.py" />

</TabItem>
</Tabs>

---

## Step 2: Create a Sling resource

Next, you'll create a <PyObject section="libraries" module="dagster_sling" object="SlingResource" /> object that contains references to the connections specified in the replication configuration:


<CodeExample path="docs_snippets/docs_snippets/integrations/sling/sling_connection_resources.py" />


A <PyObject section="libraries" module="dagster_sling" object="SlingResource" /> takes a `connections` parameter, where each <PyObject section="libraries" module="dagster_sling" object="SlingConnectionResource" /> represents a connection to a source or target database. You may provide as many connections to the `SlingResource` as needed.

The `name` parameter in the <PyObject section="libraries" module="dagster_sling" object="SlingConnectionResource" /> should match the `source` and `target` keys in the replication configuration.

You can pass a connection string or arbitrary keyword arguments to the <PyObject section="libraries" module="dagster_sling" object="SlingConnectionResource" /> to specify the connection details. Refer to [Sling's connections reference](https://docs.slingdata.io/connections/database-connections) for the specific connection types and parameters.

---

## Step 3: Define the Sling assets

Next, define a Sling asset using the <PyObject section="libraries" module="dagster_sling" object="sling_assets" decorator /> decorator. Dagster will read the replication configuration to produce assets.

Each stream will render two assets, one for the source stream and one for the target destination. You can override how assets are named by passing in a custom <PyObject section="libraries" module="dagster_sling" object="DagsterSlingTranslator" /> object.

<CodeExample
    startAfter="start_sling_assets"
    endBefore="end_sling_assets"
    path="docs_snippets/docs_snippets/integrations/sling/sling_dagster_translator.py" 
/>


---

## Step 4: Create the Definitions object

The last step is to include the Sling assets and resource in a <PyObject section="definitions" module="dagster" object="Definitions" /> object. This enables Dagster tools to load everything we've defined:

<CodeExample
    startAfter="start_sling_defs"
    endBefore="end_sling_defs"
    path="docs_snippets/docs_snippets/integrations/sling/sling_dagster_translator.py"
/>


That's it! You should now be able to view your assets in the [Dagster UI](/guides/operate/webserver) and run the replication job.

---

## Examples

### Example 1: Database to database

To set up a Sling sync between two databases, such as Postgres and Snowflake, you could do something like the following:


<CodeExample path="docs_snippets/docs_snippets/integrations/sling/postgres_snowflake.py" />


### Example 2: File to database

To set up a Sling sync between a file in an object store and a database, such as from Amazon S3 to Snowflake, you could do something like the following:


<CodeExample
    startAfter="start_storage_config"
    endBefore="end_storage_config"
    path="docs_snippets/docs_snippets/integrations/sling/s3_snowflake.py"
/>

---

## APIs in this guide

| Name                                                                                     | Description                                                                            |
|------------------------------------------------------------------------------------------| -------------------------------------------------------------------------------------- |
| <PyObject section="libraries" module="dagster_sling" object="sling_assets" decorator />  | The core Sling asset factory for building syncs                                        |
| <PyObject section="libraries" module="dagster_sling" object="SlingResource" />           | The Sling resource used for handing credentials to databases and object stores         |
| <PyObject section="libraries" module="dagster_sling" object="DagsterSlingTranslator" />  | A translator for specifying how to map between Sling and Dagster types                 |
| <PyObject section="libraries" module="dagster_sling" object="SlingConnectionResource" /> | A Sling connection resource for specifying database and storage connection credentials |

---

### About Sling

Sling provides an easy-to-use YAML configuration layer for loading data from files, replicating data between databases, exporting custom SQL queries to cloud storage, and much more.

#### Key Features

- **Data Movement**: Transfer data between different storage systems and databases efficiently

- **Flexible Connectivity**: Support for numerous databases, data warehouses, and file storage systems

- **Transformation Capabilities**: Built-in data transformation features during transfer

- **Multiple Operation Modes**: Support for various replication modes including full-refresh, incremental, and snapshot

- **Production-Ready**: Deployable with monitoring, scheduling, and error handling
