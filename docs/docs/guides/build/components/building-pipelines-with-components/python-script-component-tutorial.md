---
title: Build pipelines with Python scripts
description: Execute Python scripts as assets with Dagster components
sidebar_position: 700
---

Dagster provides a `PythonScriptComponent` that you can use to execute Python scripts as assets in your Dagster project. This component runs your Python scripts in a subprocess using [Dagster Pipes](/integrations/external-pipelines), allowing you to leverage existing Python scripts while benefiting from Dagster's orchestration and observability features. This guide will walk you through how to use the `PythonScriptComponent` to execute your Python scripts.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/1-scaffold-project.txt" />

Activate the project virtual environment:

<CliInvocationExample contents="source ../.venv/bin/activate" />

## 2. Scaffold a Python script component definition

Now that you have a Dagster project, you can scaffold a Python script component definition. In this example, we'll create a component definition called `generate_revenue_report` that will execute a Python script to process sales data and generate a revenue report.

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/2-scaffold-python-script-component.txt" />

The scaffold call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/3-tree.txt" />

## 3. Create a Python script (if needed)

Next, you will need to create a Python script that will be executed by the component if you do not already have an existing Python script you've already written. Dagster will orchestrate it without requiring changes to your code. For this example, we'll create a simple data processing script:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/4-process-sales-data.py"
  title="my-project/src/my_project/defs/generate_revenue_report/process_sales_data.py"
  language="python"
/>

This script will be executed by Dagster in a subprocess. Any output printed to `stdout/stderr` will be captured and displayed in the Dagster UI logs.

## 4. Configure your component

Update your `defs.yaml` file to specify the Python script and define the assets that will be created. You can also specify properties for the asset in Dagster, such as a group name and description:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/5-customized-component.yaml"
  title="my-project/src/my_project/defs/generate_revenue_report/defs.yaml"
  language="yaml"
/>

You can run `dg list defs` to see the asset corresponding to your component:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/7-list-defs.txt" />
</WideContent>

## 5. Launch your assets

Once your component is configured, you can launch your assets to execute the Python scripts:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/6-launch.txt" />

Navigate to the Dagster UI and you'll see your assets. To execute your Python script, click on the asset, then click **Materialize**. The script will run in a subprocess, and you'll be able to see the logs and metadata in the Dagster UI.

## Advanced configuration

### Log metadata inside Python script

For more advanced use cases, you can use [Dagster Pipes](/integrations/external-pipelines) to pass metadata from your Python script back to Dagster. This allows you to provide rich information about your assets directly in the Dagster UI:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/8-advanced-pipes-script.py"
  title="my-project/src/my_project/defs/generate_revenue_report/process_sales_data.py"
  language="python"
/>

With Dagster Pipes, you can:

- **Log structured information**: Use `context.log.info()` to send logs directly to Dagster.
- **Report asset metadata**: Use <PyObject section="libraries" integration="pipes" module="dagster_pipes" object="PipesContext" method="report_asset_materialization" displayText="context.report_asset_materialization()" /> to attach rich metadata that appears in the Dagster UI.
- **Handle errors**: Exception information is automatically captured and reported to Dagster.

### Orchestrate multiple Python scripts

You can define multiple Python script component instances in a single `defs.yaml` file using the `---` separator syntax. This allows you to run different scripts for different assets:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/9-multiple-scripts-component.yaml"
  title="my-project/src/my_project/defs/generate_revenue_report/defs.yaml"
  language="yaml"
/>

Each component instance runs independently and can execute different Python scripts. This approach is useful when you have multiple related data processing tasks that should be organized together, but run separately.

### Set up dependencies

You can specify dependencies between assets from different scripts. Using the multiple scripts example above, you can make one script depend on another:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/10-dependencies-component.yaml"
  title="my-project/src/my_project/defs/generate_revenue_report/defs.yaml"
  language="yaml"
/>

### Automate Python scripts

You can configure when assets should be automatically materialized using [declarative automation](/guides/automate/declarative-automation) conditions:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/11-automation-component.yaml"
  title="my-project/src/my_project/defs/generate_revenue_report/defs.yaml"
  language="yaml"
/>

### Creating scripts in subdirectories

You can organize your scripts in subdirectories within your component:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/12-tree-with-subdirs.txt" />

Reference scripts in subdirectories in your `defs.yaml`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/python-script-component/13-subdirectory-component.yaml"
  title="my-project/src/my_project/defs/generate_revenue_report/defs.yaml"
  language="yaml"
/>

## Best practices

- **Start simple**: Begin with standard Python scripts that print output for basic orchestration needs.
- **Log structured metadata and information with Dagster Pipes**: Use print statements for simple cases, or leverage `context.log.info()` with Pipes for structured logging and use `open_dagster_pipes()` context manager to leverage full Pipes support, such as streaming structured asset materialization events back to Dagster.
- **Keep scripts focused**: Each script should have a clear, single responsibility, and offload complex dependencies to Dagster to benefit from native observability like lineage tracking and asset metadata.
