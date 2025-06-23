---
title: Transform data
description: Transform data with dbt
sidebar_position: 20
---

A data platform typically involves various roles working together, each contributing in different ways. Some individuals will be more involved in certain areas than others. For example, with [dbt](https://www.getdbt.com/), analysts may focus primarily on modeling the data but still want their models integrated into the overall pipeline.

Next you will incorporate a dbt project to model the data. In this step, you will:

- Integrate with dbt
- Build software-defined assets for dbt models in a dbt project

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

This dbt project is already set with models that work with the raw data we brought in previously and requires no modifications.

## 2. Define the dbt Component

Now that you have a dbt project to work with, you'll install both the Dagster dbt integration and the dbt adapter for DuckDB. Add both packages to your Dagster project:

```bash
uv pip install dagster-dbt dbt-duckdb
```

Next we can scaffold our dbt component by providing the path to the dbt project we added earlier:

```bash
dg scaffold defs dagster_dbt.DbtProjectComponent transform --project-path transform/jdbt
```

This will add the directory `transform` to the `etl_tutorial` module:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/dbt.txt" />

## 3. Configure the dbt `defs.yaml`

This component generates a single file, `defs.yaml`, which configures the `dagster_dbt`.`DbtProjectComponent`. Most of the file’s contents were automatically set when we scaffolded the component and provided the path to the dbt project:

```yaml title="src/etl_tutorial/defs/transform/defs.yaml"
type: dagster_dbt.DbtProjectComponent

attributes:
  project: '{{ project_root }}/transform/jdbt'
```

The component is correctly configured for our dbt project but we need to make one addition:

<CodeExample
    path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/src/etl_tutorial/defs/transform/defs.yaml"
    language="yaml"
    title="src/etl_tutorial/defs/transform/defs.yaml"
/>

Adding in the `translation` attribute aligns the keys of our dbt models with the source tables. Associating them together ensures the proper lineage across our assets.

TODO: Screenshot

## Summary

We have now layered dbt into the project. The `etl_tutorial` module should look like this:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/step-1.txt" />

Once again you can materialize your assets within the UI or using `dg launch` from the command line. You can also use `dg` to get a full overview of the definitions in your project by executing:

```bash
dg list defs
```

This will return a table of all the definitions within the Dagster project. As we add more objects, you can rerun this command to see how our project grows.

:::info

You might be wondering about the relationship between components and assets. You can view components as organizational containers that hold assets and other Dagster objects, usually to serve a specific purpose.

In this case the dbt component create assets for each model in a dbt project. As models are added or changed within the dbt project, Dagster assets will be change accordingly.

:::

## Next steps

- Continue this tutorial with your [add a resource](/etl-pipeline-tutorial/add-a-resource)
