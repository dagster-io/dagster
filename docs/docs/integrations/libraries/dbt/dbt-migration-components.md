---
title: Migrating to dbt components
sidebar_label: Migrating to dbt components
description: How to migrate a Dagster dbt project from the Pythonic integration to the YAML component.
sidebar_position: 200
---

Dagster supports two ways to integrate with dbt: the [dbt component](/integrations/libraries/dbt) (recommended) and the [Pythonic integration library](/integrations/libraries/dbt/dbt-pythonic). If you built your Dagster and dbt project with the Pythonic integration, you can migrate to the dbt component and get the same result.

## 1. Scaffold the dbt component

The first step is to [scaffold a dbt component definition](/integrations/libraries/dbt#3-scaffold-a-dbt-component-definition). This will generate the `defs.yaml` configuration file with a path to your dbt project:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/7-component.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

## 2. Remove Pythonic definitions

Since the component handles the creation of any dbt assets in your Dagster project, as well as the configuration of the underlying resource, you can remove the explicit dbt resource creation code:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/remove_resources.py"
  title="my_project/defs/resources.py"
  language="python"
/>

You can also remove any `@dbt_assets` assets from your code:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/remove_assets.py"
  title="my_project/defs/assets.py"
  language="python"
/>

To ensure that the dbt assets have been replaced correctly, you can execute:

```
dg check defs
```

If there are still dbt assets defined via the Pythonic API, or the dbt resource is still present, you will receive a validation error due to duplication of definitions.

Assuming the check passes, you can also execute:

```
dg list defs
```

This will list all the assets in your project and allow you to see that the expected dbt assets are present.

## 3. Migrating translators (Optional)

If you had defined a custom `DagsterDbtTranslator` for your dbt project, that logic can be moved into the `defs.yaml` that was generated from scaffolding the component. For example, the custom translator:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/assets_translator.py"
  title="my_project/defs/assets.py"
  language="python"
  startAfter="start_custom_dagster_dbt_translator"
  endBefore="end_custom_dagster_dbt_translator"
/>

Can be applied to the `defs.yaml` in the following way:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/22-defs.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

## 4. Migrating incremental models (Optional)

If you had incremental models defined in your dbt project, this logic can be moved into the `defs.yaml` that was generated from scaffolding the component. For example, the partition:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/assets_incrementals.py"
  title="my_project/defs/assets.py"
  language="python"
  startAfter="start_incremental_partition"
  endBefore="end_incremental_partition"
/>

Applied to `@dbt_assets`:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/assets_incrementals.py"
  title="my_project/defs/assets.py"
  language="python"
  startAfter="start_incremental_dbt_models"
  endBefore="end_incremental_dbt_models"
/>

Can be applied to the components by doing the following. The first step is to add a new [template var](/guides/build/components/building-pipelines-with-components/using-template-variables) to your component. This will be used to define the partitions definition that will be used to partition the assets:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/18-template-vars.py"
  language="python"
  title="my_project/defs/dbt_ingest/template_vars.py"
/>

This will take the place of the `dg.DailyPartitionsDefinition` definition.

Next, apply the partition from the new template vars to the `defs.yaml` using the `post_process` field. You will also need to include configurations to the `cli_args` field so dbt can execute the using the partition:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/20-defs.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>
