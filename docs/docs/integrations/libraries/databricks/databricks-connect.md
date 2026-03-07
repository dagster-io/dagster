---
title: Databricks Connect
sidebar_position: 10
description: With Databricks Connect, you can centralize your Python code in your Dagster project while executing Spark workloads remotely on a Databricks cluster.
---

[Databricks Connect](https://docs.databricks.com/aws/en/dev-tools/databricks-connect/) allows you to centralize your Python code in your Dagster project while executing Spark workloads remotely on a Databricks cluster. Unlike job submission approaches, your code runs in the Dagster process, but Spark operations execute on Databricks compute.

## When to use Databricks Connect

Databricks Connect is best for:

- Interactive development and quick iterations
- Centralized code that doesn't need deployment to Databricks
- Moderate-sized workloads where you want simpler debugging
- Greenfield Databricks use cases

It's not suitable for:

- Large batch jobs that should run independently
- Long-running workloads that would block the Dagster process
- Scenarios where network connectivity to Databricks is unreliable

## Step 1. Prepare a Dagster project

1. To begin, you'll need a Dagster project. You can use an [existing project](/guides/build/projects/moving-to-components/migrating-project) or [create a new one](/guides/build/projects/creating-projects).

2. Activate your project virtual environment:

   ```
   source .venv/bin/activate
   ```

3. Add the `databricks-connect` library to your project:

   <Tabs>
     <TabItem value="uv" label="uv">
       <CliInvocationExample path="docs_snippets/docs_snippets/integrations/databricks/uv-add-databricks-connect.txt" />
     </TabItem>
     <TabItem value="pip" label="pip">
       <CliInvocationExample path="docs_snippets/docs_snippets/integrations/databricks/pip-install-databricks-connect.txt" />
     </TabItem>
   </Tabs>

4. Configure your environment:

   ```bash
   export DATABRICKS_HOST=https://dbc-xxxxxxx-yyyy.cloud.databricks.com/
   export DATABRICKS_TOKEN=<your-personal-access-token>
   ```

## Step 2: Write a script to run Spark operations on Databricks

Next, write a Python script that connects to Databricks to run Spark operations.

In the example below:

- The Python code runs in your Dagster deployment
- Spark DataFrame operations execute remotely on Databricks
- You have direct access to the Spark API within your asset functions
- There is no job submission overhead for interactive workloads

<CodeExample
  path="docs_snippets/docs_snippets/integrations/databricks/databricks_connect.py"
  title="src/<project-name>/defs/databricks-assets.py"
/>
