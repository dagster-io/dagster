---
title: Quickstart
description: Learn how to quickly get up and running with Dagster
last_update: 
    date: 2024-08-10
    author: Pedram Navid
---

# Dagster Tutorial: Building Your First Dagster Project

Welcome to this hands-on tutorial where you'll learn how to build a basic Extract, Transform, Load (ETL) pipeline using Dagster. By the end of this tutorial, you'll have created a functional pipeline that extracts data from a CSV file and transforms it.

## What You'll Learn

- How to set up a basic Dagster project
- How to create Software-Defined Assets (SDAs) for each step of the ETL process
- How to use Dagster's built-in features to monitor and execute your pipeline

## Prerequisites

- Basic Python knowledge
- Python 3.7+ installed on your system, see [installation guide](tutorial/installation.md) for more details

## Step 1: Set Up Your Dagster Environment

First, set up a new Dagster project.

1. Open your terminal and create a new directory for your project:

   ```bash title="Create a new directory"
   mkdir dagster-quickstart
   cd dagster-quickstart
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

## Step 2: Create Your Dagster Project Structure

Set up a basic project structure:

:::warning

The file structure here is simplified to get quickly started. 

Once you've completed this tutorial, consider the [ETL Pipeline Tutorial](/tutorial/tutorial-etl) to learn 
how to build more complex pipelines with best practices.

:::

1. Create the following files and directories:

   ```bash title="Project structure"
   dagster-quickstart/
   ├── quickstart/
   │   ├── __init__.py
   │   └── assets.py
   ├── data/
       └── sample_data.csv
   ```

   ```bash title="Create the project structure"
   mkdir quickstart data
   touch quickstart/__init__.py quickstart/assets.py
   touch data/sample_data.csv
   ```
   
   

2. Create a sample CSV file as a data source. In the `data/sample_data.csv` file, add the following content:

   ```csv
   id,name,age,city
   1,Alice,28,New York
   2,Bob,35,San Francisco
   3,Charlie,42,Chicago
   4,Diana,31,Los Angeles
   ```

## Step 3: Define Your Assets

Now, create the assets for the ETL pipeline. Open `quickstart/assets.py` and add the following code:

```python
import pandas as pd
from dagster import asset, Definitions

@asset
def processed_data():
    df = pd.read_csv("data/sample_data.csv")
    df['age_group'] = pd.cut(df['age'], bins=[0, 30, 40, 100], labels=['Young', 'Middle', 'Senior'])
    df.to_csv("data/processed_data.csv", index=False)
    return "Data loaded successfully"

defs = Definitions(assets=[processed_data])
```

This code defines a single data asset within a single computation that performs three steps:
- Reads data from the CSV file
- Adds an `age_group` column based on the `age`
- Saves the processed data to a CSV file

If you are used to task-based orchestrations, this might feel a bit different. 
In traditional task-based orchestrations, you would have three separate steps,
but in Dagster, you model your pipelines using assets as the fundamental building block,
rather than tasks.

The `Definitions` object serves as the central configuration point for a Dagster project. In this code, a `Definitions` 
object is defined and the asset is passed to it. This tells Dagster about the assets that make up the ETL pipeline 
and allows Dagster to manage their execution and dependencies.

## Step 4: Run Your Pipeline

:::warning

There should be screenshots here!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

:::

1. In the terminal, navigate to your project root directory and run:

   ```bash
   dagster dev -f quickstart/assets.py
   ```

2. Open your web browser and go to `http://localhost:3000`

3. You should see the Dagster UI along with the asset. 

3. Click Materialize All to run the pipeline.

4. In the popup that appears, click View to view a run as it executes.

5. Watch as Dagster executes your pipeline. Try different views by selecting the different view buttons in the top-left.
You can click on each asset to see its logs and metadata.

## Step 5: Verify Your Results

To verify that your pipeline worked correctly:

1. In your terminal, run:

   ```bash
   cat data/processed_data.csv
   ```

You should see your transformed data, including the new `age_group` column.

## What You've Learned

Congratulations! You've just built and run your first pipeline with Dagster. You've learned how to:

- Set up a Dagster project
- Define Software-Defined Assets for each step of your pipeline
- Use Dagster's UI to run and monitor your pipeline

## Next Steps

- Continue with the [ETL Pipeline Tutorial](/tutorial/tutorial-etl) to learn how to build a more complex ETL pipeline
- Learn how to [Think in Assets](/concepts/assets/thinking-in-assets)