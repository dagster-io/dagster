---
title: LLM fine-tuning
description: Learn how to fine-tune an LLM
last_update:
   author: Dennis Hume
sidebar_position: 10
---

# Fine-tune an LLM

In this tutorial, you'll build a pipeline with Dagster that:

- Loads a public Goodreads JSON dataset into DuckDB
- Performs feature engineering to enhance the data
- Creates and validates the data files needed for an OpenAI fine-tuning job
- Generate a custom model and validate it

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
- Familiarity with SQL and Python data manipulation libraries, such as [Pandas](https://pandas.pydata.org/).
- Understanding of data pipelines and the extract, transform, and load process (ETL).
</details>


## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Within the Dagster repo, navigate to the project:

   ```bash
   cd examples/dagster-llm-fine-tune
   ```

2. Create and activate a virtual environment:

   <Tabs>
   <TabItem value="macos" label="MacOS">
   ```bash
   uv venv dagster_tutorial
   source dagster_tutorial/bin/activate
   ```
   </TabItem>
   <TabItem value="windows" label="Windows">
   ```bash
   uv venv dagster_tutorial
   dagster_tutorial\Scripts\activate
   ```
   </TabItem>
   </Tabs>

3. Install Dagster and the required dependencies:

   ```bash
   uv pip install -e ".[dev]"
   ```

## Step 2: Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:

followed by a bash code snippet for 

```bash
dagster dev
```

## Next steps

- Continue this tutorial with [ingestion](ingestion)
