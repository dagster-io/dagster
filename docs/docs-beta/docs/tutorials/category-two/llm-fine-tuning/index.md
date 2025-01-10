---
title: LLM Fine Tuning
description: Learn how to fine tune an LLM
last_update:
   author: Dennis Hume
sidebar_position: 10
sidebar_class_name: hidden
---

# Fine-Tune an LLM

In this tutorial, you'll build a pipeline with Dagster that:

- Loads a public Goodreads JSON dataset into DuckDB
- Perform feature engineering to enhance the data
- Create and valiate the data files needed for an OpenAI fine-tuning job
- Generate a custom model and validate it

## You will learn to:

- Set up a Dagster project with the recommended project structure
- Create and materialize assets
- Create and materialize dependant assets
- Ensure data quality with asset checks

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
- Familiarity with SQL and Python data manipulation libraries, such as Pandas.
- Understanding of data pipelines and the extract, transform, and load process.
</details>


## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Open your terminal and create a new directory for your project:

   ```bash
   mkdir dagster-llm-fine-tune
   cd dagster-llm-fine-tune
   ```

2. Create and activate a virtual environment:

   <Tabs>
   <TabItem value="macos" label="MacOS">
   ```bash
   python -m venv dagster_tutorial
   source dagster_tutorial/bin/activate
   ```
   </TabItem>
   <TabItem value="windows" label="Windows">
   ```bash
   python -m venv dagster_tutorial
   dagster_tutorial\Scripts\activate
   ```
   </TabItem>
   </Tabs>

3. Install Dagster and the required dependencies:

   ```bash
   pip install dagster dagster-webserver pandas dagster-duckdb
   ```

## Step 3: Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:"

followed by a bash code snippet for `dagster dev`


## Next steps

- Continue this tutorial with [ingestion](ingestion)
