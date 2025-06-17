---
title: Build your first Dagster project
description: Learn how to set up a Dagster environment, create a project, define assets, and run your first pipeline.
sidebar_position: 30
sidebar_label: 'Quickstart'
---

Welcome to Dagster! In this guide, you'll learn:

- How to set up a basic Dagster project
- How to create a single Dagster asset that encapsulates the entire Extract, Transform, and Load (ETL) process
- How to use Dagster's UI to monitor and execute your pipeline

## Prerequisites

To follow the steps in this guide, you'll need Python 3.9+ and `uv` installed on your system. For more information, see the [Installation guide](/getting-started/installation).

## Step 1: Set up the Dagster environment

1. Open the terminal and create a new directory for your project:

   ```bash
   uvx create-dagster project dagster-quickstart
   cd dagster-quickstart
   ```

2. Activate the virtual environment:

   <Tabs>
     <TabItem value="macos" label="MacOS & Linux">
       ```source .venv/bin/activate```
     </TabItem>
     <TabItem value="windows" label="Windows">
      ```.venv\Scripts\activate```
     </TabItem>
   </Tabs>

3. Install the required dependencies in the virtual environment:

   ```bash
   uv pip install pandas
   ```

### Dagster project structure

Your new Dagster project should have the following structure:

```
.
├── pyproject.toml
├── src
│   └── dagster-quickstart
│       ├── __init__.py
│       ├── components
│       │   ├── __init__.py
│       ├── definitions.py
│       └── defs
│           └── __init__.py
├── tests
│   └── __init__.py
└── uv.lock
```

## Step 2: Scaffold an assets file

Use the [`dg scaffold defs`](/api/dg/dg-cli#dg-scaffold) command to generate an assets file on the command line:

   ```bash
   dg scaffold defs dagster.asset assets.py
   ```

   This will add a new file `assets.py` to the `defs` directory:

   ```
   .
   └── src
       └── dagster-quickstart
           └── defs
               └── assets.py
   ```

## Step 3: Add data

Next, add the `sample_data.csv` file:

   ```bash
   mkdir src/dagster-quickstart/defs/data
   touch src/dagster-quickstart/defs/data/sample_data.csv
   ```

   Within this file add the following content:

   ```csv
   id,name,age,city
   1,Alice,28,New York
   2,Bob,35,San Francisco
   3,Charlie,42,Chicago
   4,Diana,31,Los Angeles
   ```

   This CSV will act as the data source for your Dagster pipeline.

## Step 3: Define the assets

Now, create the assets for the ETL pipeline. Open `src/dagster-quickstart/defs/assets.py` file in your preferred editor and include the following code:

<CodeExample
   path="docs_snippets/docs_snippets/getting-started/quickstart.py"
   language="python"
   title="src/dagster-quickstart/defs/assets.py"
/>

:::info Asset vs task-based orchestration

This asset definition may seem unusual if you're used to task-based orchestration. In that case, you'd have three separate steps for extracting, transforming, and loading.

However, in Dagster, you'll model your pipelines using [assets](/guides/build/assets) as the fundamental building block, rather than tasks.

:::

## Step 4: Run the pipeline

1. In the terminal, navigate to your project's root directory and run:

   ```bash
   dg dev
   ```

2. Open your web browser and navigate to `http://localhost:3000`, where you should see the Dagster UI:

   ![2048 resolution](/images/getting-started/quickstart/dagster-ui-start.png)

3. In the top navigation, click **Assets > View global asset lineage**.

4. Click **Materialize** to run the pipeline.

5. In the popup that displays, click **View**. This will open the **Run details** page, allowing you to view the run as it executes.

   ![2048 resolution](/images/getting-started/quickstart/run-details.png)

   Use the **view buttons** in near the top left corner of the page to change how the run is displayed. You can also click the asset to view logs and metadata.

## Step 5: Verify the results

In your terminal, run:

```bash
cat src/dagster-quickstart/defs/data/processed_data.csv
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

- Continue with the [ETL pipeline tutorial](/etl-pipeline-tutorial/) to learn how to build a more complex ETL pipeline
- [Create your own Dagster project](/guides/build/projects/creating-a-new-project) and [add assets](/guides/build/assets/defining-assets) to it