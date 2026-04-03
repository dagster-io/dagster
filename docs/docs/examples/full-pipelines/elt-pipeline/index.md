---
title: ELT pipeline with Sling and dlt
description: Learn how to build an ELT pipeline using Sling and dlt with a component-forward approach
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/integrations/dlthub.jpeg
tags: [code-example]
canonicalUrl: '/examples/full-pipelines/elt-pipeline'
slug: '/examples/full-pipelines/elt-pipeline'
---

In this example, you'll build a full ELT pipeline that processes e-commerce order data alongside GitHub repository activity. The pipeline ingests production database tables (`users`, `orders`, `products`) and GitHub API data (`issues`, `pull_requests`) into DuckDB, then transforms them into analytics-ready summaries (`customer_order_summary`, `product_revenue`) — all using Dagster components.

The pipeline:

- Ingests database tables from [Postgres](https://www.postgresql.org/) into [DuckDB](https://duckdb.org) using [Sling](https://slingdata.io/)
- Ingests API data from the [GitHub API](https://docs.github.com/en/rest) into [DuckDB](https://duckdb.org) using [dlt](https://dlthub.com/)
- Registers both ingestion pipelines as Dagster assets using [Dagster components](/guides/build/components).
- Transforms the ingested data into analytics-ready tables using `TemplatedSqlComponent`

The entire pipeline — ingestion and transformation — is built with Dagster components. Instead of writing `@asset` functions by hand, you describe each stage in YAML and Dagster generates the asset graph. This keeps your pipeline declarative, consistent, and easy to extend.

## Prerequisites

To follow the steps in this guide, you'll need:

- Python 3.10+ and [`uv`](https://docs.astral.sh/uv) installed. For more information, see the [Installation guide](/getting-started/installation).
- A GitHub [personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens#about-personal-access-tokens) (for the dlt GitHub ingestion).
- A running [Postgres](https://www.postgresql.org/) instance (for the Sling ingestion).

## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Clone the [Dagster repo](https://github.com/dagster-io/dagster) and navigate to the project:

   ```bash
   cd examples/docs_projects/project_elt_pipeline
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

4. Ensure the following environments have been populated in your `.env` file. Start by copying the template:

   ```bash
   cp .env.example .env
   ```

   And then populate the fields.

## Step 2: Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:

```bash
dg dev
```

## Next steps

- Continue this example by [adding Sling ingestion](/examples/full-pipelines/elt-pipeline/sling-ingest)
