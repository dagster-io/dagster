---
title: Dagster integration with dbt
description: Learn how to integrate Dagster with dbt
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/integrations/dbt/dbt.svg
tags: [code-example]
canonicalUrl: '/examples/full-pipelines/dbt'
slug: '/examples/full-pipelines/dbt'
---

In this example, you'll build a pipeline with Dagster that integrates with dbt, including incremental models and tests.

## Prerequisites

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
- Familiar with [dbt](https://www.getdbt.com) and data transformation.

## 1. Set up your Dagster environment

First, set up a new Dagster project.

1. Clone the [Dagster repo](https://github.com/dagster-io/dagster) and navigate to the project:

   ```bash
   cd examples/docs_projects/project_dbt
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

## 2. Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:

```bash
dg dev
```

## Next steps

Continue this example with the [ingestion step](/examples/full-pipelines/dbt/ingestion).
