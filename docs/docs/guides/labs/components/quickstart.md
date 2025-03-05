---
title: Get started with `dg`
description: Learn how to quickly get up and running with Dagster and `dg`
sidebar_position: 30
sidebar_label: "Quickstart"
---

In this guide, you'll use Dagster's CLI `dg` to build and execute a basic pipeline that:

- Extracts data from a CSV file
- Transforms the data
- Loads the transformed data to a new CSV file

## What you'll learn

- How to set up a Dagster project
- How to create Dagster assets using components
- How to use Dagster's UI to monitor and execute your pipeline

## Prerequisites

<details>
  <summary>Prerequisites</summary>

To follow the steps in this guide, you'll need:

- Basic Python knowledge
- Python 3.9+ installed on your system. Refer to the [Installation guide](/getting-started/installation) for information.
- The python package manager `uv` and Dagster's CLI `dg`. Refer to the [`dg`
  Installation guide](/guides/labs/components/index.md#installation).
</details>

## Step 1: Initialize a Dagster workspace

Open the terminal and run `dg init`. Accept the default workspace name of
`dagster-workspace` and give the project a name of `quickstart`:

```bash
$ tmp % dg init
Enter the name of your Dagster workspace [dagster-workspace]:
Scaffolded files for Dagster workspace at /Users/smackesey/stm/tmp/dagster-workspace.
Enter the name of your first Dagster project (or press Enter to continue without creating a project): quickstart
Creating a Dagster project at /Users/smackesey/stm/tmp/dagster-workspace/projects/quickstart.
Scaffolded files for Dagster project at /Users/smackesey/stm/tmp/dagster-workspace/projects/quickstart.
...
```

Let's look at the scaffolded workspace and project:

```bash
$ cd dagster-workspace
$ tree
├── libraries
├── projects
│   └── quickstart
│       ├── pyproject.toml
│       ├── quickstart
│       │   ├── __init__.py
│       │   ├── definitions.py
│       │   └── lib
│       │       └── __init__.py
│       ├── quickstart_tests
│       │   └── __init__.py
│       └── uv.lock
└── pyproject.toml
```

:::info
You may be familiar with the concept of Python _virtual environments_. A
typical Python project starts with creating a virtual environment into which
dependencies for the project are installed. This keeps your project from
having an implicit dependency on details of the system Python installation.

Not shown in the above tree is a virtual environment that `dg` created for us
at `dagster-workspace/projects/quickstart/.venv`. This virtual environment
already contains `dagster`. When working with `dg`, for the most part you
shouldn't need to activate or worry about this virtual environment. `dg` knows
how to detect the environment and use it when necessary.
:::

The one thing missing from our scaffolded workspace is some data to work with.
Create a file:

```bash
$ mkdir data
$ touch data/sample_data.csv
```
And copy in this content:

```csv
id,name,age,city
1,Alice,28,New York
2,Bob,35,San Francisco
3,Charlie,42,Chicago
4,Diana,31,Los Angeles
```

## Step 2: Define the assets

Now we're going to create some assets for the ETL pipeline. We're going to use
components to define these assets. Let's take a look at what components are
already available in the environment that `dg` scaffolded:

```bash
cd projects/quickstart
dg list component-type
```

`PipesSubprocessScriptCollectionComponent` can suit our purposes. This
component defines a set of Dagster assets that wrap arbitrary Python scripts.
Here we'll write a single script that is wrapped by a single asset. Let's
scaffold the component:

```bash
$ dg scaffold component dagster_components.PipesSubprocessScriptCollectionComponent processed_data
```

```
from dagster_pipes import open_dagster_pipes
import pandas as pd

with open_dagster_pipes() as context:

    ## Read data from the CSV
    df = pd.read_csv("data/sample_data.csv")

    ## Add an age_group column based on the value of age
    df["age_group"] = pd.cut(
        df["age"], bins=[0, 30, 40, 100], labels=["Young", "Middle", "Senior"]
    )

    ## Save processed data
    df.to_csv("data/processed_data.csv", index=False)
```

This may seem unusual if you're used to task-based orchestration. In that case, you'd have three separate steps for extracting, transforming, and loading.

However, in Dagster, you'll model your pipelines using assets as the fundamental building block, rather than tasks.

## Step 3: Run the pipeline

1. In the terminal, pull up the Dagster UI by running `dg dev`:

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

- Continue with the [ETL pipeline tutorial](/etl-pipeline-tutorial/) to learn how to build a more complex ETL pipeline
- Learn how to [Think in assets](/guides/build/assets/)
