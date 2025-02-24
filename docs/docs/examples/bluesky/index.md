---
title: Analyzing Bluesky data
description: Learn how to build an end-to-end analytics pipeline
last_update:
   author: Dennis Hume
sidebar_position: 10
sidebar_custom_props:
  logo: images/integrations/dbt/dbt.svg
---

# Analyzing Bluesky data

:::note

To see [video of this example](https://www.youtube.com/watch?v=z3trqkKPbsI)

:::

In this example, you'll build a pipeline with Dagster that:

- Ingestion of data-related Bluesky posts
- Modelling data using dbt
- Creates and validates the data files needed for an OpenAI fine-tuning job
- Representing data in a dashboard

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
- Understanding of data pipelines and the extract, transform, and load process (ETL).
- Familiar with [dbt](https://www.getdbt.com/) and data transformation.
- Usage of BI tools for dashboards.
</details>


## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Clone the [Dagster repo](https://github.com/dagster-io/dagster) and navigate to the project:

   ```bash
   cd examples/docs_project/project_atproto_dashboard
   ```

2. Create and activate a virtual environment:

   <Tabs>
   <TabItem value="macos" label="MacOS">
   ```bash
   uv venv dagster_example
   source dagster_example/bin/activate
   ```
   </TabItem>
   <TabItem value="windows" label="Windows">
   ```bash
   uv venv dagster_example
   dagster_example\Scripts\activate
   ```
   </TabItem>
   </Tabs>

3. Install Dagster and the required dependencies:

   ```bash
   uv pip install -e ".[dev]"
   ```

4. Ensure the following environments have been populated in your .env file. Start by copying the template:

   ```bash
   cp .env.example .env
   ```

   And then populate the fields.

## Step 2: Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:

followed by a bash code snippet for 

```bash
dagster dev
```

## Next steps

- Continue this example with [ingestion](ingestion)