---
title: Analyzing Bluesky data
description: Learn how to build an end-to-end analytics pipeline
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/integrations/dbt/dbt.svg
tags: [code-example]
canonicalUrl: '/examples/bluesky'
slug: '/examples/bluesky'
---

# Analyzing Bluesky data

:::note

To see [video of this example](https://www.youtube.com/watch?v=z3trqkKPbsI)

:::

In this example, you'll build a pipeline with Dagster that:

- Ingestion of data-related Bluesky posts
- Modeling data using dbt
- Representing data in a dashboard with PowerBI

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
- Understanding of data pipelines and the extract, transform, and load process (ETL).
- Familiar with [dbt](https://www.getdbt.com) and data transformation.
- Usage of BI tools for dashboards.

</details>

## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Clone the [Dagster repo](https://github.com/dagster-io/dagster) and navigate to the project:

   ```bash
   cd examples/docs_project/project_atproto_dashboard
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

4. Ensure the following environments have been populated in your .env file. Start by copying the template:

   ```bash
   cp .env.example .env
   ```

   And then populate the fields.

## Step 2: Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:

followed by a bash code snippet for

```bash
dg dev
```

## Next steps

- Continue this example with [ingestion](/examples/bluesky/ingestion)
