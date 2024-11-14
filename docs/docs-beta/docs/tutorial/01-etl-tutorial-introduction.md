---
title: Build an ETL Pipeline
description: Learn how to build an ETL pipeline with Dagster
last_update:
  date: 2024-08-10
  author: Pedram Navid
---

# Build your first ETL pipeline

Welcome to this hands-on tutorial where you'll learn how to build an ETL pipeline with Dagster while exploring key parts of Dagster.

## What you'll learn

- Setting up a Dagster project with the recommended project structure
- Creating Assets and using Resources to connect to external systems
- Adding metadata to your assets
- Building dependencies between assets
- Running a pipeline by materializing assets
- Adding schedules, sensors, and partitions to your assets

[Add image for what the completed global asset graph looks like]

## Step 1: Set up your Dagster environment

First, set up a new Dagster project.

1. Open your terminal and create a new directory for your project:

   ```bash title="Create a new directory"
   mkdir dagster-etl-tutorial
   cd dagster-etl-tutorial
   ```

2. Create a virtual environment and activate it:

   ```bash title="Create a virtual environment"
   python -m venv dagster_tutorial 
   source dagster_tutorial/bin/activate
   # On Windows, use `dagster_tutorial\Scripts\activate`
   ```

3. Install Dagster and the required dependencies:

   ```bash title="Install Dagster and dependencies"
   pip install dagster dagster-webserver pandas dagster-duckdb
   ```

## Step 2: Copying Project Scaffold

Next we will get the raw data for the project. As well as the project scaffold, Dagster has several pre-built scaffolds you can install depending on your use case. You can see the full up to date list by running. `dagster project list-examples`

Use the project scaffold command for this project. 
   ```bash title="ETL Project Scaffold"
      dagster project from-example --example getting_started_etl_tutorial
   ```

The project should have this structure. 

```
dagster-etl-tutorial/
├── data/
│   └── products.csv
│   └── sales_data.csv
│   └── sales_reps.csv
│   └── sample_request/
│       └── request.json
├── etl_tutorial/
│   └── definitions.py
├── pyproject.toml
├── setup.cfg
├── setup.py
```

## Dagster Project Structure

In the root directory there are three configuration files that are common in Python package management. These manage dependencies and identifies the Dagster modules in the project. The etl_tutorial folder is where our Dagster definition for this code location exists. The data directory is where the raw data for the project is stored and we will reference these files in our software-defined assets. 

### File/Directory Descriptions

#### Dagster files

- **etl_tutorial/**: This is a Python module that contains your Dagster code. It is the main directory where you will define your assets, jobs, schedules, sensors, and resources.

  - **definitions.py**: This file is typically used to define jobs, schedules, and sensors. It organizes the various components of your Dagster project. This allows Dagster to load the definitions in a module.

#### Python files

- **pyproject.toml**: This file is used to specify build system requirements and package metadata for Python projects. It is part of the Python packaging ecosystem.

- **setup.cfg**: This file is used for configuration of your Python package. It can include metadata about the package, dependencies, and other configuration options.

- **setup.py**: This script is used to build and distribute your Python package. It is a standard file in Python projects for specifying package details.

## What you've learned

- Set up a Python virtual environment and installed Dagster
- Setup project scaffold
- How a Dagster project is structured and what these files do 

## Next steps

- Continue this tutorial with [your first asset](/tutorial/02-your-first-asset)
