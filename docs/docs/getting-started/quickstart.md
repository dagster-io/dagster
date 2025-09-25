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

import ProjectCreationPrereqs from '@site/docs/partials/\_ProjectCreationPrereqs.md';

<ProjectCreationPrereqs />

## Step 1: Scaffold a new Dagster project

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      1. Open your terminal and scaffold a new Dagster project:

         ```shell
         uvx create-dagster@latest project dagster-quickstart
         ```

      2. Respond `y` to the prompt to run `uv sync` after scaffolding

         ![Responding y to uv sync prompt](/images/getting-started/quickstart/uv_sync_yes.png)

      3. Change to the `dagster-quickstart` directory:

         ```shell
         cd dagster-quickstart
         ```
      4. Activate the virtual environment:

         <Tabs>
            <TabItem value="macos" label="MacOS/Unix">
               ```shell
               source .venv/bin/activate
               ```
            </TabItem>
            <TabItem value="windows" label="Windows">
               ```shell
               .venv\Scripts\activate
               ```
            </TabItem>
         </Tabs>

      5. Install the required dependencies in the virtual environment:

         ```shell
         uv add pandas
         ```

   </TabItem>

   <TabItem value="pip" label="pip">
      1. Open your terminal and scaffold a new Dagster project:

         ```shell
         create-dagster project dagster-quickstart
         ```
      2. Change to the `dagster-quickstart` directory:

         ```shell
         cd dagster-quickstart
         ```

      3. Create and activate a virtual environment:

         <Tabs>
            <TabItem value="macos" label="MacOS/Unix">
               ```shell
               python -m venv .venv
               ```
               ```shell
               source .venv/bin/activate
               ```
            </TabItem>
            <TabItem value="windows" label="Windows">
               ```shell
               python -m venv .venv
               ```
               ```shell
               .venv\Scripts\activate
               ```
            </TabItem>
         </Tabs>

      4. Install the required dependencies:

         ```shell
         pip install pandas
         ```

      5. Install your project as an editable package:

         ```shell
         pip install --editable .
         ```

   </TabItem>
</Tabs>

Your new Dagster project should have the following structure:

<Tabs groupId="package-manager">

   <TabItem value="uv" label="uv">
      ```shell
      .
      └── dagster-quickstart
         ├── pyproject.toml
         ├── src
         │   └── dagster_quickstart
         │       ├── __init__.py
         │       ├── definitions.py
         │       └── defs
         │           └── __init__.py
         ├── tests
         │   └── __init__.py
         └── uv.lock
      ```
   </TabItem>
   <TabItem value="pip" label="pip">
      ```shell
      .
      └── dagster-quickstart
         ├── pyproject.toml
         ├── src
         │   └── dagster_quickstart
         │       ├── __init__.py
         │       ├── definitions.py
         │       └── defs
         │           └── __init__.py
         └── tests
            └── __init__.py
      ```
   </TabItem>
</Tabs>

## Step 2: Scaffold an assets file

Use the [`dg scaffold defs`](/api/clis/dg-cli/dg-cli-reference#dg-scaffold) command to generate an assets file on the command line:

```shell
dg scaffold defs dagster.asset assets.py
```

This will add a new file `assets.py` to the `defs` directory:

```shell
src
└── dagster_quickstart
   ├── __init__.py
   └── defs
      ├── __init__.py
      └── assets.py
```

## Step 3: Add data

Next, create a `sample_data.csv` file. This file will act as the data source for your Dagster pipeline:

```shell
mkdir src/dagster_quickstart/defs/data && touch src/dagster_quickstart/defs/data/sample_data.csv
```

In your preferred editor, copy the following data into this file:

<CodeExample
  path="docs_snippets/docs_snippets/getting-started/quickstart/sample_data.csv"
  language="csv"
  title="src/dagster_quickstart/defs/data/sample_data.csv"
/>

## Step 4: Define the asset

To define the assets for the ETL pipeline, open `src/dagster_quickstart/defs/assets.py` file in your preferred editor and copy in the following code:

<CodeExample
  path="docs_snippets/docs_snippets/getting-started/quickstart/assets.py"
  language="python"
  title="src/dagster_quickstart/defs/assets.py"
/>

At this point, you can list the Dagster definitions in your project with [`dg list defs`](/api/clis/dg-cli/dg-cli-reference#dg-list). You should see the asset you just created:

<CliInvocationExample path="docs_snippets/docs_snippets/getting-started/quickstart/dg_list_defs.txt" />

You can also load and validate your Dagster definitions with [`dg check defs`](/api/clis/dg-cli/dg-cli-reference#dg-check):

<CliInvocationExample path="docs_snippets/docs_snippets/getting-started/quickstart/dg_check_defs.txt" />

## Step 5: Run the pipeline

1. In the terminal, navigate to your project's root directory and run:

   ```bash
   dg dev
   ```

2. Open your web browser and navigate to [http://localhost:3000](http://localhost:3000), where you should see the Dagster UI:

   ![Dagster UI](/images/getting-started/quickstart/dagster-ui-start.png)

3. In the top navigation, click **Assets > View lineage**.

4. Click **Materialize** to run the pipeline.

5. In the popup, click **View**. This will open the **Run details** page, allowing you to view the run as it executes.

   ![Run details page](/images/getting-started/quickstart/run-details.png)

   Use the **view buttons** in near the top left corner of the page to change how the run is displayed. You can also click the asset to view logs and metadata.

:::tip

You can also run the pipeline by using the [`dg launch --assets`](/api/clis/dg-cli/dg-cli-reference#dg-launch) command and passing an [asset selection](/guides/build/assets/asset-selection-syntax):

```
dg launch --assets "*"
```

:::

## Step 6: Verify the results

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

- Follow the [Tutorial](/dagster-basics-tutorial) to learn how to build a more complex ETL pipeline
- [Create your own Dagster project](/guides/build/projects/creating-a-new-project) and [add assets](/guides/build/assets/defining-assets) to it
- Check out our [Python primer series](https://dagster.io/blog/python-packages-primer-1) for an in-depth tour of Python modules, packages and imports
