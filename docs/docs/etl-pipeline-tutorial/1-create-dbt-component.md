---
title: Create dbt component
description: Transform data with dbt
sidebar_position: 20
---

Next you will use [dbt](https://www.getdbt.com/) to model the data ingested with Sling. In this step, you will:

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

## 2. Define the dbt Component

Now that there is a dbt project to work with, we will install the Dagster dbt integration as well as the dbt adaptor for DuckDB. Add both to your Dagster project:

```bash
uv pip install dagster-dbt dbt-duckdb
```

Now we can scaffold our dbt component, providing a path to the dbt project that added above:

```bash
dg scaffold defs dagster_dbt.DbtProjectComponent transform --project-path transform/jdbt
```

This will add the directory `transform` to the `etl_tutorial` module:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/dbt.txt" />

## 3. Configure the dbt component

This component only generates a single file, `defs.yaml`, to configure the `dagster_dbt.DbtProjectComponent` component.  Most of this file was configured when we scaffolded the component and provided the path to the dbt project:

```yaml
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

Adding in the `translation` attribute aligns the keys of our dbt models with the source tables from Sling. Associating them together ensures the proper lineage of our assets.

TODO: Screenshot

## Summary

Sling and dbt are both layered into our Dagster project. The `etl_tutorial` module should look like this:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/etl_tutorial/tree/step-1.txt" />

Once again you can materialize your assets within the UI or using `dg launch` from the command line. You can also use `dg` to get a full overview of the definitions in your project by executing:

```bash
dg list defs
```

This will return a table of all the definitions within the Dagster project. As we add more objects, you can rerun this command to see how our project grows.

## Next steps

- Continue this tutorial with your [create and materialize assets](/etl-pipeline-tutorial/create-and-materialize-assets)
