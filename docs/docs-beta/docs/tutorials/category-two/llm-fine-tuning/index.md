---
title: LLM Fine Tuning
description: Learn how to fine tune an LLM
last_update:
   author: Dennis Hume
sidebar_position: 10
sidebar_class_name: hidden
---

# Fine-Tune an LLM

In this tutorial, you'll build an pipeline with Dagster that:

- Imports data from Goodreads DuckDB
- Does feature engineering to enhance the data
- Creates and validates a training and validation file
- Executes an OpenAI fine-tuning job and validates the model

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

## Step 2: Create the Dagster project structure

Run the following command to create the project directories and files for this tutorial:

   ```bash 
      dagster project from-example --example getting_started_llm_fine_tune
   ```

Your project should have this structure:
{/* vale off */}
```
dagster-llm-fine-tune/
├── data/
│   └── products.csv
│   └── sales_data.csv
│   └── sales_reps.csv
│   └── sample_request/
│       └── request.json
├── llm_fine_tune/
│   └── definitions.py
├── pyproject.toml
├── setup.cfg
├── setup.py
```
{/* vale on */}

:::info
Dagster has several example projects you can install depending on your use case. To see the full list, run `dagster project list-examples`. For more information on the `dagster project` command, see the [API documentation](https://docs-preview.dagster.io/api/cli#dagster-project).
::: 

### Dagster project structure

#### dagster-llm-fine-tune root directory

In the `dagster-llm-fine-tune` root directory, there are three configuration files that are common in Python package management. These files manage dependencies and identify the Dagster modules in the project.
| File | Purpose |
|------|---------|
| pyproject.toml | This file is used to specify build system requirements and package metadata for Python projects. It is part of the Python packaging ecosystem. |
| setup.cfg | This file is used for configuration of your Python package. It can include metadata about the package, dependencies, and other configuration options. |
| setup.py | This script is used to build and distribute your Python package. It is a standard file in Python projects for specifying package details. |

#### llm_fine_tune directory

This is the main directory where you will define your assets, jobs, schedules, sensors, and resources.
| File | Purpose |
|------|---------|
| definitions.py | This file is typically used to define jobs, schedules, and sensors. It organizes the various components of your Dagster project. This allows Dagster to load the definitions in a module. |

#### data directory

The data directory contains the raw data files for the project. We will reference these files in our software-defined assets in the next step of the tutorial.

## Step 3: Launch the Dagster webserver

To make sure Dagster and its dependencies were installed correctly, navigate to the project root directory and start the Dagster webserver:"

followed by a bash code snippet for `dagster dev`


## Next steps

- Continue this tutorial by [ingestion](ingestion)
