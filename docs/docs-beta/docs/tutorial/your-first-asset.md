---
title: Your First Asset 
description: Get the project data and create your first Asset
last_update:
  date: 2024-10-11
  author: Alex Noonan
---

# Your First Software Defined Asset

## Step 1: Create Dagster Project Files

Dagster needs several project files to run. 


1. Create Config file

  ```bash title="Create Config file"
    echo -e "[metadata]\nname = dagster_etl_tutorial" > setup.cfg
  ```

2. Create Setup Python File

  ```bash title="Create Setup file"
    echo > setup.py
  ```

In this file we will be creating the environemnt for Dagster to run our project. One thing in particular we need to do is define our Python dependencies. Open that python file and put the following code in there. 


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

idk what this does but its in there. use scout for this:


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