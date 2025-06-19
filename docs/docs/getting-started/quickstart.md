---
title: Build your first Dagster pipeline
description: Learn how to set up a Dagster environment, create a project, define assets, and run your first pipeline.
sidebar_position: 30
sidebar_label: 'Quickstart'
---

Welcome to Dagster! In this guide, we'll cover:

- Setting up a basic Dagster project
- Creating a single Dagster [asset](/guides/build/assets) that encapsulates the entire Extract, Transform, and Load (ETL) process
- Using Dagster's UI to monitor and execute your pipeline

:::info Prerequisites

To follow the steps in this guide, you'll need Python 3.9+ and `uv` installed on your system. For more information, see the [Installation guide](/getting-started/installation).

:::

## Step 1: Scaffold a new Dagster project

1. Open the terminal and scaffold a new Dagster project:

   ```bash
   uvx -U create-dagster project dagster-quickstart && cd dagster-quickstart
   ```

2. Activate the virtual environment:

   <Tabs>
     <TabItem value="macos" label="MacOS/Unix">
       ```
       source .venv/bin/activate
       ```
     </TabItem>
     <TabItem value="windows" label="Windows">
      ```
      .venv\Scripts\activate
      ```
     </TabItem>
   </Tabs>

3. Install the required dependencies in the virtual environment:

   ```bash
   uv pip install pandas
   ```

Your new Dagster project should have the following structure:

```
.
├── pyproject.toml
├── src
│   └── dagster_quickstart
│       ├── __init__.py
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
   src
   └── dagster_quickstart
      ├── __init__.py
      └── defs
         ├── __init__.py
         └── assets.py
   ```

## Step 3: Add data

Next, create a `sample_data.csv` file. This file will act as the data source for your Dagster pipeline:

   ```bash
   mkdir src/dagster_quickstart/defs/data && touch src/dagster_quickstart/defs/data/sample_data.csv
   ```

  In your preferred editor, copy the following data into this file:

   ```csv
   id,name,age,city
   1,Alice,28,New York
   2,Bob,35,San Francisco
   3,Charlie,42,Chicago
   4,Diana,31,Los Angeles
   ```

## Step 3: Define the asset

To define the assets for the ETL pipeline, open `src/dagster-quickstart/defs/assets.py` file in your preferred editor and copy in the following code:

<CodeExample
   path="docs_snippets/docs_snippets/getting-started/quickstart.py"
   language="python"
   title="src/dagster_quickstart/defs/assets.py"
/>

At this point, you can list the Dagster definitions in your project with [`dg list defs`](/api/dg/dg-cli#dg-list), which should include the asset you just created:

```
dg list defs
```

```
┏━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ Section ┃ Definitions                                               ┃
┡━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ Assets  │ ┏━━━━━━━━━━━━━━━━┳━━━━━━━━━┳━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┓ │
│         │ ┃ Key            ┃ Group   ┃ Deps ┃ Kinds ┃ Description ┃ │
│         │ ┡━━━━━━━━━━━━━━━━╇━━━━━━━━━╇━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━┩ │
│         │ │ processed_data │ default │      │       │             │ │
│         │ └────────────────┴─────────┴──────┴───────┴─────────────┘ │
└─────────┴───────────────────────────────────────────────────────────┘
```

You can also load and validate your Dagster definitions with [`dg check defs`](/api/dg/dg-cli#dg-check):

```
dg check defs
```

```
All components validated successfully.
All definitions loaded successfully.
```

## Step 4: Run the pipeline

1. In the terminal, navigate to your project's root directory and run:

   ```bash
   dg dev
   ```

2. Open your web browser and navigate to `http://localhost:3000`, where you should see the Dagster UI:

   ![Dagster UI showing processed_data asset in lineage graph](/images/getting-started/quickstart/dagster-ui-start.png)

3. Click **Materialize** to run the pipeline.

4. In the popup that displays, click **View**. This will open the **Run details** page, allowing you to view the run as it executes.

   ![2048 resolution](/images/getting-started/quickstart/run-details.png)

   Use the **view buttons** in near the top left corner of the page to change how the run is displayed. You can also click the asset to view logs and metadata.

:::tip

You can also run the pipeline by using the [`dg launch --assets`](/api/dg/dg-cli#dg-launch) command and passing an [asset selection](/guides/build/assets/asset-selection-syntax/):

```
dg launch --assets "*"
```
:::

## Step 5: Verify the results

In your terminal, run:

```bash
cat src/dagster_quickstart/defs/data/processed_data.csv
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