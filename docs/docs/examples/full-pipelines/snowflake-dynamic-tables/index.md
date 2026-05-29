---
title: Snowflake Dynamic Tables as virtual assets
description: Learn how to represent Snowflake-managed Dynamic Tables as virtual assets in Dagster for correct lineage, automation, and freshness monitoring
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/integrations/snowflake.svg
tags: [code-example]
canonicalUrl: '/examples/full-pipelines/snowflake-dynamic-tables'
slug: '/examples/full-pipelines/snowflake-dynamic-tables'
---

In this example, you'll build a pipeline with Dagster that:

- Represents [Snowflake Dynamic Tables](https://docs.snowflake.com/en/user-guide/dynamic-tables-intro) as `AssetSpec(is_virtual=True)` — unexecutable in Dagster, refreshed automatically by Snowflake
- Preserves full asset lineage through virtual assets to real upstream sources
- Monitors Dynamic Table refresh state with a sensor that emits `AssetObservation` events and asset checks that report a pass/fail health signal
- Triggers a downstream asset from that same sensor — firing a run only _after_ a Dynamic Table's refresh actually lands, so the downstream never reads stale data

## Prerequisites

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.10+ installed on your system. For more information, see the [Installation guide](/getting-started/installation).
- A Snowflake account with a warehouse

## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Clone the [Dagster repo](https://github.com/dagster-io/dagster) and navigate to the project:

   ```bash
   cd examples/docs_projects/project_snowflake_dynamic_tables
   ```

2. Install the required dependencies with `uv`:

   ```bash
   uv sync
   ```

3. Activate the virtual environment:

   <Tabs>
     <TabItem value="macos" label="MacOS">
       ```source .venv/bin/activate ```
     </TabItem>
     <TabItem value="windows" label="Windows">
       ```.venv\Scripts\activate ```
     </TabItem>
   </Tabs>

4. Copy `.env.example` to `.env` and fill in your Snowflake credentials:

   ```bash
   cp .env.example .env
   ```

## Step 2: Create the Snowflake tables

Run the DDL in `sql/create_dynamic_tables.sql` against your Snowflake account to create the source tables and Dynamic Tables used in this example.

## Step 3: Launch the Dagster webserver

Navigate to the project root directory and start the Dagster webserver:

```bash
dg dev
```

## Next steps

Continue this example by [defining virtual assets](/examples/full-pipelines/snowflake-dynamic-tables/virtual-assets).
