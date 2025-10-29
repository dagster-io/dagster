---
title: Build your first Dagster pipeline
description: Learn how to set up a Dagster environment, create a project, define assets, and run your first pipeline.
sidebar_label: Quickstart (Dagster+ Hybrid and OSS)
---

Welcome to Dagster! In this guide, we'll cover:

- Setting up a basic Dagster project using Dagster OSS for local development
- Creating a single Dagster [asset](/guides/build/assets) that encapsulates the entire Extract, Transform, and Load (ETL) process
- Using Dagster's UI to monitor and execute your pipeline
- Deploying your changes to the cloud

:::info Dagster+ Serverless users

If you have created a project through the Dagster+ Serverless UI, see the [Dagster+ Serverless quickstart guide](/getting-started/serverless-quickstart) instead.

:::

## Prerequisites

Before getting started, you will need to make sure you install the following prerequisites:
* Python 3.9+
* **If using uv as your package manager**, you will need to install `uv` (**Recommended**).
* **If using pip as your package manager**, you will need to install the `create-dagster` CLI with Homebrew, `curl`, or `pip`.

For detailed instructions, see the [Installation guide](/getting-started/installation).

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

## Step 5: Start the webserver and run your pipeline

1. In the terminal, navigate to your project's root directory and run:

   ```bash
   dg dev
   ```

2. Open your web browser and navigate to [http://localhost:3000](http://localhost:3000), where you should see the Dagster UI:

   ![Dagster UI overview](/images/getting-started/quickstart-serverless/oss-ui-overview.png)

3. In the top navigation, click the **Assets** tab, then click **View lineage**:

   ![Dagster UI asset lineage page](/images/getting-started/quickstart/assets-view-lineage.png)

4. To run the pipeline, click **Materialize**:

   ![Dagster asset lineage page with materialize button](/images/getting-started/quickstart/materialize-button.png)

5. To view the run as it executes, click the **Runs** tab, then on the right side of the page, click **View**:

   ![Dagster run view](/images/getting-started/quickstart/run-view.png)

   To change how the run is displayed, you can use the **view buttons** in the top left corner of the page:

   <img src="/images/getting-started/quickstart/run-view-options.png" height="100" />

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

## Step 7. Deploy to the cloud (Optional)

Once you have run your pipeline locally, you can optionally deploy it to the cloud.

<Tabs>
   <TabItem value="oss" label="OSS">
   To deploy to OSS:
   1. Set up an [OSS deployment](/deployment/oss), if you haven't already.
   2. Add a `workspace.yaml` file to the root directory of your project. For more information, see the [`workspace.yaml` reference](deployment/code-locations/workspace-yaml).
   3. TK - what else?
   </TabItem>
   <TabItem value="hybrid" label="Dagster+ Hybrid">
   1. Set up a [Hybrid deployment](/deployment/dagster-plus/hybrid), if you haven't already.
   2. In the root directory of your project, run [`dg scaffold build-artifacts`](/api/clis/dg-cli/dg-cli-reference#dg-scaffold-build-artifacts) to create a `build.yaml` deployment configuration file and a Dockerfile.
   3. To deploy to the cloud, you can perform a one-time deployment with the [`dagster-cloud` CLI](/api/clis/dagster-cloud-cli) or [set up CI/CD](/deployment/dagster-plus/deploying-code/ci-cd/ci-cd-in-hybrid) for continuous deployment.
   </TabItem>
</Tabs>

## Next steps

Congratulations! You've just built and run your first pipeline with Dagster. Next, you can:

- Follow the [Tutorial](/dagster-basics-tutorial) to learn how to build a more complex ETL pipeline
- [Create your own Dagster project](/guides/build/projects/creating-a-new-project) and [add assets](/guides/build/assets/defining-assets) to it
- Check out our [Python primer series](https://dagster.io/blog/python-packages-primer-1) for an in-depth tour of Python modules, packages and imports
