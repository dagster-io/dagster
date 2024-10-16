---
title: Build an ETL Pipeline
description: Learn how to build an ETL pipeline with Dagster
last_update:
  date: 2024-08-10
  author: Pedram Navid
---

# Build your first ETL pipeline

Welcome to this hands-on tutorial where you'll learn how to build an ETL pipeline with Dagster while exploring key parts of Dagster.
If you haven't already, complete the [Quick Start](/getting-started/quickstart) tutorial to get familiar with Dagster.

## What you'll learn

- Setting up a Dagster project with the recommended project structure
- Creating Assets and using Resources to connect to external systems
- Adding metadata to your assets
- Building dependencies between assets
- Running a pipeline by materializing assets
- Adding schedules, sensors, and partitions to your assets

## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Open your terminal and create a new directory for your project:

   ```bash title="Create a new directory"
   mkdir dagster-etl-tutorial
   cd dagster-etl-tutorial
   ```

2. Create a virtual environment and activate it:

   ```bash title="Create a virtual environment"
   python -m venv venv
   source venv/bin/activate
   # On Windows, use `venv\Scripts\activate`
   ```

3. Install Dagster and the required dependencies:

   ```bash title="Install Dagster and dependencies"
   pip install dagster dagster-webserver pandas
   ```

## Step 2: Copying Data Files

Next we will get the raw data for the project. 

1. Create a new folder for the raw data:

   ```bash title="Create the data directory"
   mkdir data
   cd data
   ```

2. Copy the raw csv files:

   ```bash title="Copy the csv files"
   curl -L -o products.csv https://raw.githubusercontent.com/dagster-io/dagster/refs/heads/master/examples/docs_beta_snippets/docs_beta_snippets/guides/tutorials/etl_tutorial/data/products.csv

   curl -L -o sales_reps.csv https://raw.githubusercontent.com/dagster-io/dagster/refs/heads/master/examples/docs_beta_snippets/docs_beta_snippets/guides/tutorials/etl_tutorial/data/sales_reps.csv

   curl -L -o sales_data.csv https://raw.githubusercontent.com/dagster-io/dagster/refs/heads/master/examples/docs_beta_snippets/docs_beta_snippets/guides/tutorials/etl_tutorial/data/sales_data.csv  
   ```
3. Copy Sample Request json file

   ```bash title="Create the sample request"
   mkdir sample_request
   cd sample_request
   curl -L -o request.json https://raw.githubusercontent.com/dagster-io/dagster/refs/heads/master/examples/docs_beta_snippets/docs_beta_snippets/guides/tutorials/etl_tutorial/data/sample_request/request.json
   
   # navigating back to the root directory
   cd../..
   ```



## What you've learned

- Set up a Python virtual environment and installed Dagster
- Copied raw data for project

## Next steps

- Continue this tutorial with [setting up your dagster project ](/tutorial/dagster-project-setup)
