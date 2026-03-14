---
title: Components
description: Defining custom components
sidebar_position: 90
---

So far, we have built our pipeline out of existing `Definitions`, but this is not the only way to include `Definitions` in a Dagster project.

If we think about the code for our three assets (`customers`, `orders`, and `payments`), it is all very similar. Each asset performs the same action, turning an S3 file into a DuckDB table, while differing only in the URL path and table name.

These assets are a great candidate for a [custom component](/guides/build/components/creating-new-components). Components generate `Definitions` through a configuration layer. There are built-in components that let you integrate with common workflows (such as turning Python scripts into assets), or dynamically generate `Definitions` for tools like [dbt](/integrations/libraries/dbt) or [Fivetran](/integrations/libraries/fivetran). With custom components, you can define your own specific use cases.

In this step, you will use a custom component to streamline the development of similar assets and replace their `Definitions` in your project with a Component that can generate them from a YAML configuration file instead.

![2048 resolution](/images/tutorial/dagster-tutorial/overviews/components.png)

## 1. Scaffold a custom component

First, scaffold a custom component using `dg`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/commands/dg-create-custom-component.txt" />

This adds a new directory, `components`, within `src/dagster_tutorial`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/tree/step-6a.txt" />

This directory contains the files needed to define the custom component.

## 2. Define the custom component

When designing a component, keep its interface in mind. In this case, the assets that the component will create share the following attributes:

- A DuckDB database shared across all assets.
- A list of ETL assets, each with a URL path and a table name.

The first step is to create a `dg.Model` for the ETL assets. `dg.Model` turns any class that inherits from it into a [Pydantic](https://docs.pydantic.dev/) model. This model is then used to implement the YAML interface from the component.

This model will contain the two attributes that define an asset:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/src/dagster_tutorial/components/tutorial.py"
  language="python"
  startAfter="start_etl_model"
  endBefore="end_etl_model"
  title="src/etl_tutorial/components/tutorial.py"
/>

Next, add the interface to the `dg.Component` class. In this case, there will be a single attribute for the DuckDB database and a list of the `ETL` models you just defined:

```python
    duckdb_database: str
    etl_steps: list[ETL]
```

The rest of the code will look very similar to the asset definitions you wrote earlier. The `build_defs` method constructs a `Definitions` object containing all the Dagster objects created by the component. Based on the interface defined at the class level, you will generate multiple ETL assets. The final Dagster object to include is the `resource` that the assets rely on, which can also be set with an attribute.

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/src/dagster_tutorial/components/tutorial.py"
  language="python"
  startAfter="start_tutorial_component"
  endBefore="end_tutorial_component"
  title="src/etl_tutorial/components/tutorial.py"
/>

Run the check again to ensure that the component code is correct:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/commands/dg-check-defs.txt" />

## 3. Scaffold the component definition

If you list your components again, you should see that the custom component is now registered:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/commands/dg-list-components-custom.txt" />

You can now scaffold definitions from it just like any other component:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/commands/dg-scaffold-custom-component.txt" />

This adds a new directory, `tutorials`, within `defs`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/tree/step-6b.txt" />

## 4. Configure the component

To configure the component, update the YAML file created when you scaffolded a definition from the component:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/src/dagster_tutorial/components/defs.yaml"
  language="yaml"
  title="src/dagster_tutorial/defs/tutorial/defs.yaml"
/>

## 5. Remove the old definitions

Before running `dg check` again, remove the `customers`, `orders`, and `payments` assets from `assets.py` and the `resource.py` file. The component is now responsible for generating these objects (otherwise there will be duplicate keys in the asset lineage).

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster_tutorial/tree/step-6c.txt" />

## 6. Materialize the assets

When you materialize your assets in the Dagster UI at [http://127.0.0.1:3000/assets](http://127.0.0.1:3000/assets), you should see that the asset graph looks the same as before.

## Summary

Congratulations! You've just built a fully functional, end-to-end data pipeline. This is no small feat! You've laid the foundation for a scalable, maintainable, and observable data platform.

## Recommended next steps

- Join our [Slack community](https://dagster.io/slack).
- Continue learning with [Dagster University](https://courses.dagster.io) courses.
- Start a [free trial of Dagster+](https://dagster.cloud/signup) for your own project.
