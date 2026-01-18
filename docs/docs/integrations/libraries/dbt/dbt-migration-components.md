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

## 3. Migrating custom translators (Optional)

If you had defined a custom `DagsterDbtTranslator` for your dbt project, the **recommended approach** is to create a custom subclass of `DbtProjectComponent` and override the `get_asset_spec` method. This provides more flexibility and type safety than YAML configuration.

For example, the custom translator:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/assets_translator.py"
  title="my_project/defs/assets.py"
  language="python"
  startAfter="start_custom_dagster_dbt_translator"
  endBefore="end_custom_dagster_dbt_translator"
/>

Can be migrated to a custom component by creating a new Python file:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/custom_component_translator.py"
  title="my_project/lib/custom_dbt_component.py"
  language="python"
  startAfter="start_custom_component_translator"
  endBefore="end_custom_component_translator"
/>

Then reference this custom component in your `defs.yaml`:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/custom_component_translator_defs.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

This approach maps translator methods to component methods:

- `get_asset_key()` → Override `get_asset_spec()` and customize the `key` attribute
- `get_group_name()` → Override `get_asset_spec()` and customize the `group_name` attribute
- `get_description()` → Override `get_asset_spec()` and customize the `description` attribute
- `get_metadata()` → Override `get_asset_spec()` and customize the `metadata` attribute

### Alternative: YAML configuration

For simpler customizations, you can also use YAML configuration with the `translation` field:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/12-customized-component.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

## 4. Migrating incremental models (Optional)

If you had incremental models defined in your dbt project, the **recommended approach** is to create a custom subclass of `DbtProjectComponent` and override the `execute` method. This allows you to customize the dbt CLI arguments based on partition information.

For example, the partitioned incremental models:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/assets_incrementals.py"
  title="my_project/defs/assets.py"
  language="python"
  startAfter="start_incremental_dbt_models"
  endBefore="end_incremental_dbt_models"
/>

Can be migrated to a custom component by creating a new Python file:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/custom_component_incremental.py"
  title="my_project/lib/incremental_dbt_component.py"
  language="python"
  startAfter="start_custom_component_incremental"
  endBefore="end_custom_component_incremental"
/>

To use this custom component, you'll also need to define the partition definition. First, add a new [template var](/guides/build/components/building-pipelines-with-components/using-template-variables) to define the partitions:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/18-template-vars.py"
  language="python"
  title="my_project/defs/dbt_ingest/template_vars.py"
/>

Then reference the custom component and apply the partition in your `defs.yaml`:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/pythonic/custom_component_incremental_defs.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

### Alternative: YAML configuration with cli_args

For simpler cases where you don't need custom logic, you can use YAML configuration with the `cli_args` field:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/20-defs.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>
