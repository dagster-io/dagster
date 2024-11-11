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

## What you've learned

Congratulations! You've just built and run your first ETL pipeline with Dagster. You've learned how to:

- Set up a Dagster project
- Define Software-Defined Assets for each step of your ETL process
- Use Dagster's UI to run and monitor your pipeline

## Next steps

To expand on this tutorial, you could:

- Add more complex transformations
- Implement error handling and retries
- Create a schedule to run your pipeline periodically
