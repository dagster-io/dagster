---
title: Databricks Asset Bundle Component
sidebar_position: 30
description: The Databricks Asset Bundle Component integrates with Databricks Asset Bundles to provide a way to define Databricks jobs, pipelines, and configuration as code using YAML.
---

:::note Preview

`DatabricksAssetBundleComponent` is currently in **preview**. The API may change in future releases.

:::

The <PyObject section="libraries" integration="databricks" module="dagster_databricks" object="DatabricksAssetBundleComponent" /> integrates with [Databricks Asset Bundles](https://docs.databricks.com/en/dev-tools/bundles/index.html) to provide a way to define Databricks jobs, pipelines, and configuration as code using YAML. The component reads your `databricks.yml` bundle configuration and automatically creates Dagster assets from the job tasks (notebook, Python wheel, Spark Python, Spark JAR, etc.) defined within it, with dependency information preserved. When the assets are materialized, Dagster submits the tasks to Databricks and monitors execution.

This approach is well suited for teams that are already using Databricks Asset Bundles to manage their Databricks workflows and want to bring them into Dagster without rewriting job definitions.

The component supports the following Databricks task types:

- [Notebook tasks](https://docs.databricks.com/aws/en/dev-tools/bundles/job-task-types#clean-room-notebook-task)
- [Python script tasks](https://docs.databricks.com/aws/en/dev-tools/bundles/job-task-types#python-script-task)
- [Python wheel tasks](https://docs.databricks.com/aws/en/dev-tools/bundles/job-task-types#python-wheel-task)
- [JAR tasks](https://docs.databricks.com/aws/en/dev-tools/bundles/job-task-types#jar-task)
- [Run job tasks](https://docs.databricks.com/aws/en/dev-tools/bundles/job-task-types#run-job-task)
- [Condition tasks](https://docs.databricks.com/aws/en/dev-tools/bundles/job-task-types#condition-task)

## Step 1: Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-asset-bundle-component/1-scaffold-project.txt" />

Activate the project virtual environment:

```
source ../.venv/bin/activate
```

Finally, add the `dagster-databricks` library to the project:

<PackageInstallInstructions packageName="dagster-databricks" />

## Step 2: Scaffold the component definition

Now that you have a Dagster project, you can scaffold a `DatabricksAssetBundleComponent` component definition. You'll need to provide:

- A path for the `databricks.yml` configuration file
- The URL of your Databricks workspace host
- The name of the environment variable that stores your Databricks workspace token

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-asset-bundle-component/2-scaffold-defs.txt" />

The `dg scaffold defs` call will generate a `defs.yaml` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-asset-bundle-component/3-tree.txt" />

The `defs.yaml` defines the component in your project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-asset-bundle-component/defs.yml" />

## Step 3: Customize component configuration

### Compute configuration

You can specify how tasks should be executed on Databricks using one of three Databricks compute options:

<Tabs>
<TabItem value="serverless" label="Serverless (default)">

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-asset-bundle-component/defs-serverless.yml" />

</TabItem>
<TabItem value="new_cluster" label="New cluster">

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-asset-bundle-component/defs-new-cluster.yml" />

</TabItem>
<TabItem value="existing_cluster" label="Existing cluster">

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-asset-bundle-component/defs-existing-cluster.yml" />

</TabItem>
</Tabs>

### Custom asset mapping

By default, the Databricks Asset Bundle Component creates one Dagster asset per Databricks task. You can override this by providing a custom mapping from task keys to asset specs:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/databricks-components/databricks-asset-bundle-component/defs-custom-mapping.yml" />
