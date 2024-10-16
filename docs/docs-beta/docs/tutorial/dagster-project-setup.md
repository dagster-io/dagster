---
title: Dagster Project Setup
description: Learn how to setup a Dagster project from scratch
last_update:
  date: 2024-10-16
  author: Alex Noonan
---

# Dagster Project Setup

## What you'll learn

- Setting up a Dagster project with the recommended project structure
- Creating Assets and using Resources to connect to external systems
- Adding metadata to your assets
- Building dependencies between assets
- Running a pipeline by materializing assets
- Adding schedules, sensors, and partitions to your assets


## Step 1: Create Dagster Project Files

Dagster needs several project files to run. These files are common in Python Package managment and help manage project configurationa dn dependencies. 

The setup.cfg file is an INI-style configuration file that contains option defaults for setup.py commands. 

1. Create Config file

  ```bash title="Create Config file"
    echo -e "[metadata]\nname = dagster_etl_tutorial" > setup.cfg
  ```

2. Create Setup Python File

The setup.py file is a build script for configuring Python packages. In a Dagster project, you use setup.py to defin any Python packages your project depends on, including Dagster itself. 

  ```bash title="Create Setup file"
    echo > setup.py
  ```


Open that python file and put the following code in there. 


  ```python title="Setup.py"
    from setuptools import find_packages, setup

    setup(
        name="dagster_etl_tutorial",
        packages=find_packages(exclude=["dagster_etl_tutorial_tests"]),
        install_requires=[
            "dagster",
            "dagster-cloud",
            "duckdb"
        ],
        extras_require={"dev": ["dagster-webserver", "pytest"]},
    )
  ```
3. Create Toml file

The pyproject.toml file is a configuation file that specifices package core metadata in a static, tool agnostic way. 


  ```bash title="Create Pyproject file"
    echo > pyproject.toml
  ```

  Open that file up and add the following

  ```toml
    [build-system]
    requires = ["setuptools"]
    build-backend = "setuptools.build_meta"

    [tool.dagster]
    module_name = "dagster_tutorial.definitions"
    code_location_name = "dagster_tutorial"
  ```

4. Create Dagster Python Module and Definitions file


## Next we will create our Python Definitions file 

1. Create ETL tutorial directory

   ```bash title="Create the tutorial directory"
   mkdir dagster-etl-tutorial
   cd dagster-etl-tutorial
   ```

2. Create Dagster Definitions File

In this guide we will use a simplified project structure to focus on core Dagster concepts. To accomplish this all of our code will be in one definitons file. 


  ```bash title="Create definitions.py file"
    echo > definitions.py
  ```

## What you've learned

- Set up a Python virtual environment and installed Dagster
- Copied raw data for project

## Next steps

- Continue this tutorial with your [first asset](/tutorial/your-first-asset)