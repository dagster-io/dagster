---
title: Transform data
description: Transform data with dbt
sidebar_position: 20
---

A data platform typically involves people in various roles working together, each contributing in different ways. Some individuals will be more involved in certain areas than others. For example, with [dbt](https://www.getdbt.com/), analysts may focus primarily on modeling the data, but still want their models integrated into the overall pipeline.

In this step, we will incorporate a dbt project to model the data we loaded with DuckDB.


## 1. Add the dbt project

First we will need a dbt project to work with. Run the following to add a dbt project to the root of the `etl_tutorial`:

```bash
git clone --depth=1 https://github.com/dagster-io/jaffle-platform.git transform && rm -rf transform/.git
```

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

```bash
uv pip install dagster-dbt dbt-duckdb
```

Next, we can scaffold a dbt component definition by providing the path to the dbt project we added earlier:

```bash
dg scaffold defs dagster_dbt.DbtProjectComponent transform --project-path transform/jdbt
```

This will add the directory `transform` to the `etl_tutorial` module:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/dbt.txt" />

## 3. Configure the dbt `defs.yaml`

The dbt component creates a single file, `defs.yaml`, which configures the `dagster_dbt`.`DbtProjectComponent`. Most of the file’s contents were generated when we scaffolded the component and provided the path to the dbt project:

```yaml title="src/etl_tutorial/defs/transform/defs.yaml"
type: dagster_dbt.DbtProjectComponent

attributes:
  project: '{{ project_root }}/transform/jdbt'
```

The component is correctly configured for our dbt project, but we need to make one addition:

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/transform/defs.yaml"
    language="yaml"
    title="src/etl_tutorial/defs/transform/defs.yaml"
/>

Adding in the `translation` attribute aligns the keys of our dbt models with the source tables. Associating them together ensures the proper lineage across our assets.

![2048 resolution](/images/tutorial/etl-tutorial/ingest-assets-run.png)

## Summary

We have now layered dbt into the project. The `etl_tutorial` module should look like this:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/step-1.txt" />

Once again you can materialize your assets within the UI or using `dg launch` from the command line. You can also use [`dg list`](/api/dg/dg-cli#dg-list) to get a full overview of the definitions in your project by executing:

```bash
dg list defs
```

This will return a table of all the definitions within the Dagster project. As we add more objects, you can rerun this command to see how our project grows.

:::info

You might be wondering about the relationship between components and definitions. Components. At a high level you a component builds a definition for a specific purpose.

**Components** are objects that programmatically build assets and other Dagster objects. They accept specific parameters and use them to build the actual definitions you need. In the case of `DbtProjectComponent`, this would be the dbt project path and the definitions it creates are the assets for each dbt model.


**Definitions** are objects that combine metadata about an entity with a Python function that defines how it behaves -- for example, when we used the `@asset` decorator on the functions for our DuckDB ingestion. This tells Dagster both what the asset is and how to materialize it.

:::

## Next steps

In the next step, we will [add a DuckDB resource](/etl-pipeline-tutorial/add-a-resource) to our project.
