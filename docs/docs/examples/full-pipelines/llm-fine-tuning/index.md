---
title: LLM fine-tuning with OpenAI
description: Learn how to fine-tune an LLM
last_update:
  author: Dennis Hume
sidebar_custom_props:
  logo: images/integrations/openai.svg
tags: [code-example]
canonicalUrl: '/examples/full-pipelines/llm-fine-tuning'
slug: '/examples/full-pipelines/llm-fine-tuning'
---

# Fine-tune an LLM

:::note

To see [video of this example](https://www.youtube.com/watch?v=x-1R2z0eEdg)

:::

In this example, you'll build a pipeline with Dagster that:

- Loads a public Goodreads JSON dataset into DuckDB
- Performs feature engineering to enhance the data
- Creates and validates the data files needed for an OpenAI fine-tuning job
- Generate a custom model and validate it

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
- Familiarity with SQL and Python data manipulation libraries, such as [Pandas](https://pandas.pydata.org).
- Understanding of data pipelines and the extract, transform, and load process (ETL).

</details>

## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Clone the [Dagster repo](https://github.com/dagster-io/dagster) and navigate to the project:

   ```bash
   cd examples/docs_projects/project_llm_fine_tune
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

## Step 2: Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:

```bash
dg dev
```

## Next steps

- Continue this example with [ingestion](/examples/full-pipelines/llm-fine-tuning/ingestion)
