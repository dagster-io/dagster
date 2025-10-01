---
title: Transform data
description: Transform data with dbt
sidebar_position: 20
---

A data platform typically involves people in various roles working together, each contributing in different ways. Some individuals will be more involved in certain areas than others. For example, with [dbt](https://www.getdbt.com), analysts may focus primarily on modeling the data, but still want their models integrated into the overall pipeline.

In this step, we will incorporate a dbt project to model the data we loaded with DuckDB.

## 1. Add the dbt project

First we will need a dbt project to work with. Run the following to add a dbt project to the root of the `etl_tutorial`:

<CliInvocationExample contents="git clone --depth=1 https://github.com/dagster-io/jaffle-platform.git transform && rm -rf transform/.git" />

There will now be a directory `transform` within the root of the project containing our dbt project.

```
.
├── pyproject.toml
├── src
├── tests
├── transform # dbt project
└── uv.lock
```

:::note

This dbt project already contains models that work with the raw data we brought in previously and requires no modifications.

:::

## 2. Scaffold a dbt component definition

Now that we have a dbt project to work with, we need to install both the Dagster dbt integration and the dbt adapter for DuckDB:

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
      Install the required dependencies:

         ```shell
         uv add dagster-dbt dbt-duckdb
         ```

   </TabItem>

   <TabItem value="pip" label="pip">
      Install the required dependencies:

         ```shell
         pip install dagster-dbt dbt-duckdb
         ```

   </TabItem>
</Tabs>

We still want our dbt project to be represented as assets in our graph, but we will define them in a slightly different way. In the previous step, we manually defined our assets by writing functions decorated with the <PyObject section="assets" module="dagster" object="asset" decorator />. This time, we will use [components](/guides/build/components), which are predefined ways to interact with common integrations or patterns. In this case, we will use the [dbt component](/integrations/libraries/dbt) to quickly turn our dbt project into assets.

The dbt component was installed when we installed the `dagster-dbt` library. This means we can now scaffold a dbt component definition with `dg scaffold defs` command:

<CliInvocationExample path="docs_projects/project_etl_tutorial/commands/dg-scaffold-dbt.txt" />

This will look similar to scaffolding assets, though also include the `--project-path` flag to set the directory of our dbt project. After the `dg` command runs, the directory `transform` is added to the `etl_tutorial` module:

<CliInvocationExample path="docs_projects/project_etl_tutorial/tree/dbt.txt" />

## 3. Configure the dbt `defs.yaml`

The dbt component creates a single file, `defs.yaml`, which configures the Dagster dbt component definition. Unlike the assets file, which was in Python, components provide a low-code interface in YAML. Most of the YAML file’s contents were generated when we scaffolded the component definition with `dg` and provided the path to the dbt project which is set in the `project` attribute under `attributes`:

```yaml title="src/etl_tutorial/defs/transform/defs.yaml"
type: dagster_dbt.DbtProjectComponent

attributes:
  project: '{{ project_root }}/transform/jdbt'
```

To check that Dagster can load the dbt component definition correctly in the top-level `Definitions` object, run `dg check` again:

<CliInvocationExample path="docs_projects/project_etl_tutorial/commands/dg-check-defs.txt" />

The component is correctly configured for our dbt project, but we need to make one addition to the YAML file:

<CodeExample
  path="docs_projects/project_etl_tutorial/src/etl_tutorial/defs/transform/defs.yaml"
  language="yaml"
  title="src/etl_tutorial/defs/transform/defs.yaml"
/>

Adding in the `translation` attribute aligns the keys of our dbt models with the assets we defined previously. Associating them together ensures the proper lineage across our assets.

![2048 resolution](/images/tutorial/etl-tutorial/ingest-assets-run.png)

## 4. Materialize assets

To materialize the assets:

1. Click **Assets**, then click "View global asset lineage" to see all of your assets.
2. Click **Materialize all**.

:::tip

You can also materialize your assets from the command line with the `dg launch` command.

:::

## Summary

We have now layered dbt into the project. The `etl_tutorial` module should look like this:

<CliInvocationExample path="docs_projects/project_etl_tutorial/tree/step-1.txt" />

Regardless of how your assets are added to your project, they will all appear together within the asset graph.

:::info

You might be wondering about the relationship between components and definitions. At a high level, a component builds a definition for a specific purpose.

**Components** are objects that programmatically build assets and other Dagster objects. They accept specific parameters and use them to build the actual definitions you need. In the case of `DbtProjectComponent`, this would be the dbt project path and the definitions it creates are the assets for each dbt model.

**Definitions** are objects that combine metadata about an entity with a Python function that defines how it behaves -- for example, when we used the `@asset` decorator on the functions for our DuckDB ingestion. This tells Dagster both what the asset is and how to materialize it.

:::

## Next steps

In the next step, we will [add a DuckDB resource](/examples/full-pipelines/etl-pipeline/add-a-resource) to our project to more efficiently manage our database connections.
