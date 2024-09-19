---
title: "Dagster quickstart"
description: Learn how to quickly get up and running with Dagster
sidebar_position: 30
sidebar_label: "Quickstart"
---

# Build your first Dagster project

Welcome to Dagster! In this guide, you'll use Dagster to create a basic pipeline that:

- Extracts data from a CSV file
- Transforms the data
- Loads the transformed data to a new CSV file

## What you'll learn

- How to set up a basic Dagster project
- How to create a Dagster asset for each step of the Extract, Transform, and Load (ETL) process
- How to use Dagster's UI to monitor and execute your pipeline

## Prerequisites

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.8+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
</details>

## Step 1: Set up the Dagster environment

1. Open the terminal and create a new directory for your project:

   ```bash
   mkdir dagster-quickstart
   cd dagster-quickstart
   ```

2. Create and activate a virtual environment:

   <Tabs>
   <TabItem value="macos" label="MacOS">
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```
   </TabItem>
   <TabItem value="windows" label="Windows">
   ```bash
   python -m venv venv
   source venv\Scripts\activate
   ```
   </TabItem>
   </Tabs>

3. Install Dagster and the required dependencies:

   ```bash
   pip install dagster dagster-webserver pandas
   ```

## Step 2: Create the Dagster project structure

:::info
The project structure in this guide is simplified to allow you to get started quickly. When creating new projects, use `dagster project scaffold` to generate a complete Dagster project.
:::

Next, you'll create a basic Dagster project that looks like this:

```
dagster-quickstart/
├── quickstart/
│   ├── __init__.py
│   └── assets.py
├── data/
    └── sample_data.csv
```

1. To create the files and directories outlined above, run the following:

   ```bash
   mkdir quickstart data
   touch quickstart/__init__.py quickstart/assets.py
   touch data/sample_data.csv
   ```

2. In the `data/sample_data.csv` file, add the following content:

   ```csv
   id,name,age,city
   1,Alice,28,New York
   2,Bob,35,San Francisco
   3,Charlie,42,Chicago
   4,Diana,31,Los Angeles
   ```

   This CSV will act as the data source for your Dagster pipeline.

## Step 3: Define the assets

Now, create the assets for the ETL pipeline. Open `quickstart/assets.py` and add the following code:

<CodeExample filePath="getting-started/quickstart.py" language="python" />

This may seem unusual if you're used to task-based orchestration. In that case, you'd have three separate steps for extracting, transforming, and loading.

However, in Dagster, you'll model your pipelines using assets as the fundamental building block, rather than tasks.

## Step 4: Run the pipeline

1. In the terminal, navigate to your project's root directory and run:

   ```bash
   dagster dev -f quickstart/assets.py
   ```

2. Open your web browser and navigate to `http://localhost:3000`, where you should see the Dagster UI:

   ![2048 resolution](/images/getting-started/quickstart/dagster-ui-start.png)

3. In the top navigation, click **Assets > View global asset lineage**.

4. Click **Materialize** to run the pipeline.

5. In the popup that displays, click **View**. This will open the **Run details** page, allowing you to view the run as it executes.

   ![Screenshot of Dagster Asset Lineage](/img/placeholder.svg)

   Use the **view buttons** in near the top left corner of the page to change how the run is displayed. You can also click the asset to view logs and metadata.

## Step 5: Verify the results

In your terminal, run:

```bash
cat data/processed_data.csv
```

You should see the transformed data, including the new `age_group` column:

```bash
id,name,age,city,age_group
1,Alice,28,New York,Young
2,Bob,35,San Francisco,Middle
3,Charlie,42,Chicago,Senior
4,Diana,31,Los Angeles,Middle
```

## Next steps

Congratulations! You've just built and run your first pipeline with Dagster. Next, you can:

- Continue with the [ETL pipeline tutorial](/tutorial/tutorial-etl) to learn how to build a more complex ETL pipeline
- Learn how to [Think in assets](/concepts/assets/thinking-in-assets)
