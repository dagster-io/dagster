---
title: Dagster & dbt (Component)
sidebar_label: dbt
sidebar_position: 1
description: Orchestrate your dbt transformations directly with Dagster.
tags: [dagster-supported, etl, component]
source: https://github.com/dagster-io/dagster/tree/master/python_modules/libraries/dagster-dbt
pypi: https://pypi.org/project/dagster-dbt/
sidebar_custom_props:
  componentAvailable: true
  logo: images/integrations/dbt/dbt.svg
partnerlink: https://www.getdbt.com/
canonicalUrl: '/integrations/libraries/dbt'
slug: '/integrations/libraries/dbt'
---

The [`dagster-dbt` library](/integrations/libraries/dbt/dagster-dbt) provides a `DbtProjectComponent` which can be used to easily represent dbt models as assets in Dagster. Dagster assets understand dbt at the level of individual dbt models. This means that you can:

- Use Dagster's UI or APIs to run subsets of your dbt models, seeds, and snapshots.
- Track failures, logs, and run history for individual dbt models, seeds, and snapshots.
- Define dependencies between individual dbt models and other data assets. For example, put dbt models after the Fivetran-ingested table that they read from, or put a machine learning after the dbt models that it's trained from.

:::info

`DbtProjectComponent` is a [state-backed component](/guides/build/components/state-backed-components), which compiles and caches your dbt project's manifest. For information on managing component state, see [Configuring state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components).

:::

:::tip dbt Fusion

Dagster supports the dbt Fusion engine as of the 1.11.5 release. Support is in preview and has known limitations, including no supported column-level metadata or column lineage. For setup instructions and the full list of gaps, see [Dagster & dbt Fusion](/integrations/libraries/dbt/dbt-fusion).

:::

## Step 1: Prepare a Dagster project

To begin, you'll need a Dagster project. You can use an [existing components-ready project](/guides/build/projects/moving-to-components/migrating-project) or create a new one:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/1-scaffold-project.txt" />

Activate the project virtual environment:

<CliInvocationExample contents="source .venv/bin/activate" />

Then, add the `dagster-dbt` library to the project, along with a duckdb adapter:

<PackageInstallInstructions packageName="dagster-dbt dbt-duckdb" />

## Step 2: Set up a dbt project

<Tabs groupId="dbt-project-location">
<TabItem value="colocate" label="Colocate with Dagster">

For this tutorial, we'll use the jaffle shop dbt project as an example. Clone it into your project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/3-jaffle-clone.txt" />

We will create a `profiles.yml` file in the `dbt` directory to configure the project to use DuckDB:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/4-profiles.yml"
  title="dbt/profiles.yml"
  language="yaml"
/>

</TabItem>
<TabItem value="external" label="External Git repository">

If your dbt project lives in a separate Git repository, you don't need to clone it locally. For this tutorial, we'll use the [Jaffle Platform](https://github.com/dagster-io/jaffle-platform) example repository, which already has a `profiles.yml` configured.

:::info

When using an external Git repository, Dagster manages the project as part of [component state](/guides/build/components/state-backed-components). For details on how state is managed, see [Configuring state-backed components](/guides/build/components/state-backed-components/configuring-state-backed-components).
:::

</TabItem>
</Tabs>

## Step 3: Scaffold a dbt component definition

<Tabs groupId="dbt-project-location">
<TabItem value="colocate" label="Colocate with Dagster">

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

</TabItem>
<TabItem value="external" label="External Git Repository">

Now that you have a Dagster project, you can scaffold a dbt component definition that points to an external Git repository. You'll need to provide the Git URL and the path to the dbt project within the repository:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/remote-1-scaffold-dbt-component.txt" />

The `dg scaffold defs` call will generate a `defs.yaml` file in your project structure:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/remote-2-tree.txt" />

In its scaffolded form, the `defs.yaml` file contains the configuration for your remote dbt project:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/remote-3-component.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

:::tip Private repositories

In some cases, you may need to provide an authentication token for private Git repositories. You can do this by adding the `token` field to your `defs.yaml` file:

```yaml
type: dagster_dbt.DbtProjectComponent

attributes:
  project:
    repo_url: https://some-host.com/your-org/your-dbt-project.git
    repo_relative_path: path/to/dbt
    token: '{{ env.GIT_TOKEN }}'
```

For Github-based repositories, this is typically unnecessary, as your credentials will be available locally as well as in the Github Actions that require access to the repository.

:::

</TabItem>
</Tabs>

This is sufficient to load your dbt models as assets. You can use `dg list defs` to see the asset representation:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/8-list-defs.txt" />
</WideContent>

## Step 4: Run your dbt models

To execute your dbt models, you can use the `dg launch` command to kick off a run through the CLI:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/9-dbt-run.txt" />

:::tip

You can also pass an [asset selection](https://docs.dagster.io/guides/build/assets/asset-selection-syntax) to the [dg launch --assets](https://docs.dagster.io/api/clis/dg-cli/dg-cli-reference#dg-launch) command:

```bash
dg launch --assets "key:'customers' and key:'orders'"
```

:::

## Step 5: Select or exclude specific models

You can control which dbt models are included in your component using the `select` or `exclude` attributes. This allows you to filter which models are represented as assets, using [dbt's selection syntax](https://docs.getdbt.com/reference/node-selection/syntax). For example, to include only the `customers` model:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/10-customized-component.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/11-list-defs.txt" />
</WideContent>

Note that `stg_customers`, `stg_orders`, and `stg_payments` still appear even though only `customers` was selected. `customers` declares them as dependencies, so Dagster creates a stub [external asset](/guides/build/assets/external-assets) for each one to keep the graph connected. These stubs have no group, kinds, or description, and Dagster will never execute them — only `customers` is actually built by this component.

To pull the upstream models in as real dbt assets instead, use [dbt's graph operators](https://docs.getdbt.com/reference/node-selection/graph-operators) in your selection:

```yaml
select: '+customers'
```

## Step 6: Customize dbt assets

### Customize dbt asset metadata

You can customize the properties of the assets emitted by each dbt model using the `translation` key in your `defs.yaml` file. This allows you to modify asset metadata such as group names, descriptions, and other properties:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/12-customized-component.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/13-list-defs.txt" />
</WideContent>

`translation` accepts any attribute of an asset spec: `key`, `key_prefix`, `deps`, `description`, `metadata`, `group_name`, `owners`, `tags`, `kinds`, `code_version`, `skippable`, `automation_condition`, `partitions_def`, and `freshness_policy`. To see the full schema — types, defaults, and per-field documentation — run:

```bash
dg utils inspect-component dagster_dbt.DbtProjectComponent --defs-yaml-schema
```

### Assign asset groups based on dbt model directory

A common pattern is to assign different asset group names based on the dbt model's directory structure (e.g., `staging`, `intermediate`, `marts`). You can achieve this using a [template variable](/guides/build/components/building-pipelines-with-components/using-template-variables) that inspects the model's `fqn` (fully qualified name).

The `node` object available in the `translation` key is the raw node dictionary for the model from your project's `manifest.json`, so every field dbt records there is available. The most commonly used ones are:

- `node.name` - the model name
- `node.fqn` - the fully qualified name as a list (for example, `["jaffle_shop", "staging", "stg_customers"]`)
- `node.original_file_path` - the path to the model file
- `node.tags` - tags defined in dbt
- `node.config` - model configuration

See dbt's [manifest.json reference](https://docs.getdbt.com/reference/artifacts/manifest-json) for the full set of fields. The Python API exposes this same dictionary to <PyObject section="libraries" integration="dbt" module="dagster_dbt" object="DagsterDbtTranslator" /> methods as `dbt_resource_props`.

#### 1. Create a template variable

First, create a template variable that extracts the group name from the `fqn`. A template variable is invoked once at load time and whatever it returns becomes the value in scope, so a variable that needs a per-model argument has to return a _function_, which you then call from `defs.yaml`:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/group-template-vars.py"
  title="my_project/defs/dbt_ingest/template_vars.py"
  language="python"
/>

#### 2. Reference the template variable in defs.yaml

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/group-defs.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

With this configuration, models in `models/staging/` will be assigned to the `staging` group, models in `models/marts/` to the `marts` group, and so on.

## Step 7: Connect upstream assets to dbt sources

If your dbt models depend on data produced by other Dagster assets (e.g., data ingested by Sling, Fivetran, or custom Python assets), you can connect them using dbt sources with Dagster metadata.

### Step 7.1: Define dbt sources with Dagster asset keys

In your dbt project, create a `sources.yml` file that maps dbt sources to Dagster asset keys using the `meta.dagster.asset_key` configuration:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/upstream-source.yml"
  title="dbt/models/sources.yml"
  language="yaml"
/>

### Step 7.2: Create upstream assets

Next, create Dagster assets that produce the source data. The asset key must match the `asset_key` defined in your dbt sources (see step 7.1):

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/component/upstream-asset.py"
  title="my_project/defs/ingest/assets.py"
  language="python"
/>

Dagster creates these connections by reading your dbt models. Whenever a dbt model references a source via `source()`, Dagster links the corresponding upstream asset to that model. In the asset graph UI, you'll see each upstream asset connected to the dbt models that reference it.

:::tip

This pattern works with any ingestion tool. For example, if you're using [Sling](/integrations/libraries/sling) or [Fivetran](/integrations/libraries/fivetran), configure the `asset_key` in your dbt sources to match the keys produced by those components.

:::

## Step 8: Add dbt asset dependencies in other components

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

## Step 9: Model incremental models as partitioned assets

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

:::note

`partitions_def` is also a valid `translation` key, so `translation: {partitions_def: '{{ daily_partitions_def }}'}` produces the same result here. `post_processing` is used above because it applies the partitions definition to every asset the component produces in one place; use `translation` when the partitions definition needs to vary based on the `node`.

:::

Finally, we need to pass in new configuration to the `cli_args` field so that the dbt execution actually changes based on what partition is executing. In particular, we want to pass in values to the `--vars` configuration field that determine the range of time that our incremental models should process.

The specific format of this configuration depends on your specific dbt project setup, but one common pattern is to use a `start_date` and `end_date` parameter for this purpose.

When the `cli_args` field is resolved, three partition template variables are in scope:

| Variable                | Description                                                                           |
| ----------------------- | ------------------------------------------------------------------------------------- |
| `partition_key`         | The key of the partition being materialized, as a string (for example, `2024-01-15`). |
| `partition_key_range`   | The `start` and `end` partition keys of the range being materialized.                 |
| `partition_time_window` | The `start` and `end` `datetime`s of the range being materialized.                    |

These are top-level names, not attributes of the `context` scope used elsewhere in `defs.yaml`. On a run with no partition they resolve to `None`, so only reference them from a component whose assets are all partitioned.

`partition_time_window` is Dagster's representation of the time range that should be processed on the current run. It can be converted into a format recognized by your dbt project using template variables:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/20-defs.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

Dagster will automatically convert this configuration dictionary into the JSON-encoded string that is expected by the dbt CLI.

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/21-list-defs.txt" />
</WideContent>

### Mixing partitioned and unpartitioned models

A single component can define both partitioned and unpartitioned assets. Narrow the `post_processing` target from `"*"` to an [asset selection](/guides/build/assets/asset-selection-syntax) matching only your incremental models, and the rest stay unpartitioned:

```yaml
post_processing:
  assets:
    - target: 'key:orders_incremental or key:events_incremental'
      attributes:
        partitions_def: '{{ daily_partitions_def }}'
```

The catch is that `cli_args` is defined once for the whole component. On a run that materializes only the unpartitioned models, `partition_time_window` is `None` and a template like `{{ partition_time_window.start.strftime('%Y-%m-%d') }}` fails. Unless your `cli_args` avoid the partition variables, keep partitioned and unpartitioned models in separate `DbtProjectComponent` instances.

Two _different_ partitions definitions always require separate components, because Dagster cannot materialize assets with differing partitions definitions in a single run. Use the `select` option to filter each component to the models it owns.

### Microbatch incremental models

dbt's microbatch strategy has a different batching model than regular incremental, see [Microbatch incremental models](/integrations/libraries/dbt/dbt-patterns#microbatch-incremental-models). The key difference for `cli_args` is that you use `--event-time-start` and `--event-time-end` instead of `--vars`:

:::note

`--vars` only passes values into the model SQL. It does **not** control which batches the microbatch engine runs.

:::

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/20b-microbatch-defs.yaml"
  title="my_project/defs/dbt_ingest/defs.yaml"
  language="yaml"
/>

The `partition_key` template variable is the string key of the active partition (e.g. `2024-01-15` for a daily partition), which matches the ISO 8601 date format expected by dbt's microbatch engine. `partition_time_window.end` provides the exclusive end of the window. Your `PartitionsDefinition` should match the model's `batch_size`, and `start_date` should match the model's `begin` config.

## Step 10: Customize manifest generation

By default, `DbtProjectComponent` runs `dbt parse --quiet` to generate the manifest during development. If you need `dbt compile` instead — for example, to access `compiled_code` on your dbt nodes — you can set the `prepare_project_cli_args` option on the `project` attribute:

```yaml
# defs.yaml
type: dagster_dbt.DbtProjectComponent

attributes:
  project:
    project_dir: '{{ project_root }}/path/to/dbt_project'
    prepare_project_cli_args: ['compile', '--quiet']
```

This passes the specified arguments to the dbt CLI when generating the manifest, instead of the default `["parse", "--quiet"]`. Using `compile` is useful when you want to leverage `node.compiled_code` in translations or custom subclasses, for example to include the compiled SQL in asset descriptions.

## Step 11: Enable Dagster+ Insights

If you are using [Dagster+](/deployment/dagster-plus) with a Snowflake or BigQuery warehouse, you can associate dbt query costs with the produced asset materializations in the [Insights](/guides/observe/insights) dashboard. Add `insights` to the `include_metadata` list:

```yaml
# defs.yaml
type: dagster_dbt.DbtProjectComponent

attributes:
  project: '{{ project_root }}/path/to/dbt_project'
  include_metadata:
    - insights
```

This can be combined with other metadata options:

```yaml
attributes:
  project: '{{ project_root }}/path/to/dbt_project'
  include_metadata:
    - column_metadata
    - row_count
    - insights
```

:::note

Insights requires `dagster-cloud` to be installed and an `InsightsSnowflakeResource` or `InsightsBigQueryResource` to be configured. For full setup instructions, see the [Snowflake Insights](/guides/observe/insights/snowflake) or [BigQuery Insights](/guides/observe/insights/google-bigquery) guides.

:::

## Advanced configuration (subclassing)

For more complex use cases that cannot easily be handled with templated yaml, you can create a custom subclass of `DbtProjectComponent` to add custom behavior. This allows you to:

- Add custom op configuration using `op_config_schema`
- Override the `get_asset_spec` method to add custom metadata
- Override the `execute` method to customize how dbt commands are executed

To do this, we can create a new subclass of the `DbtProjectComponent` in our `lib` directory. This component adds a `full_refresh` runtime config option and custom metadata:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/22-custom_dbt_component.py"
  title="my_project/lib/custom_dbt_component.py"
  language="python"
/>

This component can then be swapped in for the standard `DbtProjectComponent` in our `defs.yaml` file by updating the `type` field to reference the new component:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/23-custom-dbt-defs.yaml"
  title="my_project/defs/custom_dbt/defs.yaml"
  language="yaml"
/>

The custom component will be loaded and used just like the standard `DbtProjectComponent`:

<WideContent maxSize={1100}>
  <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/integrations/dbt-component/25-list-custom-defs.txt" />
</WideContent>

### Configuring the custom component at runtime

When you use a custom component with an `op_config_schema`, you can provide config values at runtime through the Dagster UI or when launching runs from the CLI. For example:

```yaml
ops:
  dbt_injest:
    config:
      full_refresh: true
```

This allows you to control the behavior of your dbt runs without modifying the component definition itself.
