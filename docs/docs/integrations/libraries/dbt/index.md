---
title: Dagster & dbt (Component)
sidebar_label: dbt
description: Orchestrate your dbt transformations directly with Dagster.
tags: [dagster-supported, etl]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dbt
pypi: https://pypi.org/project/dagster-dbt/
sidebar_custom_props:
  logo: images/integrations/dbt/dbt.svg
partnerlink: https://www.getdbt.com/
canonicalUrl: '/integrations/libraries/dbt'
slug: '/integrations/libraries/dbt'
---

The [`dagster-dbt` library](/api/libraries/dagster-dbt) provides a `DbtProjectComponent` which can be used to easily represent dbt models as assets in Dagster. Dagster assets understand dbt at the level of individual dbt models. This means that you can:

- Use Dagster's UI or APIs to run subsets of your dbt models, seeds, and snapshots.
- Track failures, logs, and run history for individual dbt models, seeds, and snapshots.
- Define dependencies between individual dbt models and other data assets. For example, put dbt models after the Fivetran-ingested table that they read from, or put a machine learning after the dbt models that it's trained from.

## 1. Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/1-scaffold-project.txt" />

Activate the project virtual environment:

<CliInvocationExample contents="source .venv/bin/activate" />

Then, add the `dagster-dbt` library to the project, along with a duckdb adapter:

<PackageInstallInstructions packageName="dagster-dbt dbt-duckdb" />

## 2. Set up a dbt project

For this tutorial, we'll use the jaffle shop dbt project as an example. Clone it into your project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/3-jaffle-clone.txt" />

We will create a `profiles.yml` file in the `dbt` directory to configure the project to use DuckDB:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/4-profiles.yml"
  title="dbt/profiles.yml"
  language="yaml"
/>

## 3. Scaffold a dbt component definition

Now that you have a Dagster project with a dbt project, you can scaffold a dbt component definition. You'll need to provide the path to your dbt project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/5-scaffold-dbt-component.txt" />

The `dg scaffold defs` call will generate a `defs.yaml` file in your project structure:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/6-tree.txt" />

In its scaffolded form, the `defs.yaml` file contains the configuration for your dbt project:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/7-component.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

This is sufficient to load your dbt models as assets. You can use `dg list defs` to see the asset representation:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/8-list-defs.txt" />
</WideContent>

## 4. Run your dbt models

To execute your dbt models, you can use the `dg launch` command to kick off a run through the CLI:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/9-dbt-run.txt" />

:::tip

You can also pass an [asset selection](https://docs.dagster.io/guides/build/assets/asset-selection-syntax) to the [dg launch --assets](https://docs.dagster.io/api/clis/dg-cli/dg-cli-reference#dg-launch) command:

```bash
dg launch --assets "key:'customers' and key:'orders'"
```

:::

## 5. Select or exclude specific models

You can control which dbt models are included in your component using the `select` or `exclude` attributes. This allows you to filter which models are represented as assets, using [dbt's selection syntax](https://docs.getdbt.com/reference/node-selection/syntax). For example, to include only the `customers` model:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/10-customized-component.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/11-list-defs.txt" />
</WideContent>

## 6. Customize dbt assets

You can customize the properties of the assets emitted by each dbt model using the `translation` key in your `defs.yaml` file. This allows you to modify asset metadata such as group names, descriptions, and other properties:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/12-customized-component.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/13-list-defs.txt" />
</WideContent>

## 7. Depending on dbt assets in other components

If you want to refer to assets built by the dbt component elsewhere in your Dagster project, you can use the `asset_key_for_model` method on the dbt component.
This lets you refer to an asset by the model name without having to know how that model is translated to an asset key.

Imagine a `PythonScriptComponent` that exports the `customers` model to a CSV file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/14-scaffold-python-script-component.txt" />

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/15-touch-export-customers.txt" />

You can refer to the `customers` asset in this component by using the `asset_key_for_model` method on the dbt component:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/16-component.yaml"
  title="my_project/defs/my_python_script/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/17-list-defs.txt" />
</WideContent>

## 8. Handling incremental models

If you have incremental models in your dbt project, you can model these as partitioned assets, and update the command that is used to run the dbt models to pass in `--vars` based on the range of partitions that are being processed.

The first step is to add a new [template var](/guides/build/components/building-pipelines-with-components/using-template-variables) to your component. This will be used to define the partitions definition that will be used to partition the assets.

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/18-template-vars.py"
  language="python"
  title="my_project/defs/dbt_ingest/template_vars.py"
/>

The next step is to update the `defs.yaml` file to use the new template var and apply this partitions definition to all assets using the `post_process` field:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/19-defs.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

Finally, we need to pass in new configuration to the `cli_args` field so that the dbt execution actually changes based on what partition is executing. In particular, we want to pass in values to the `--vars` configuration field that determine the range of time that our incremental models should process.

The specific format of this configuration depends on your specific dbt project setup, but one common pattern is to use a `start_date` and `end_date` parameter for this purpose.

When the `cli_args` field is resolved, it has access to a `context.partition_time_window` object, which is Dagster's representation of the time range that should be processed on the current run. This can be converted into a format recognized by your dbt project using template variables:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/20-defs.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

Dagster will automatically convert this configuration dictionary into the JSON-encoded string that is expected by the dbt CLI.

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/21-list-defs.txt" />
</WideContent>

If you have multiple different partitions definitions, you will need to create separate `DbtProjectComponent` instances for each `PartitionsDefinition` you want to use. You can filter each component to a selection of dbt models using the `select` configuration option.
