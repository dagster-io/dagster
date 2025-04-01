---
title: 'dagster-dbt integration reference'
description: Dagster can orchestrate dbt alongside other technologies.
---

:::note

Using dbt Cloud? Check out the [dbt Cloud with Dagster guide](/integrations/libraries/dbt/dbt-cloud).

:::

This reference provides a high-level look at working with dbt models through Dagster's [software-defined assets](/guides/build/assets/) framework using the [`dagster-dbt` integration library](/api/python-api/libraries/dagster-dbt).

For a step-by-step implementation walkthrough, refer to the [Using dbt with Dagster asset definitions tutorial](/integrations/libraries/dbt/using-dbt-with-dagster).

## Relevant APIs

| Name                                                                                                    | Description                                                                                                                                                                     |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`dagster-dbt project scaffold`](/api/python-api/libraries/dagster-dbt#scaffold)                        | A CLI command to initialize a new Dagster project for an existing dbt project.                                                                                                  |
| <PyObject section="libraries" module="dagster_dbt" object="dbt_assets" decorator />                     | A decorator used to define Dagster assets for dbt models defined in a dbt manifest.                                                                                             |
| <PyObject section="libraries" module="dagster_dbt" object="DbtCliResource" />                           | A class that defines a Dagster resource used to execute dbt CLI commands.                                                                                                       |
| <PyObject section="libraries" module="dagster_dbt" object="DbtCliInvocation" />                         | A class that defines the representation of an invoked dbt command.                                                                                                              |
| <PyObject section="libraries" module="dagster_dbt" object="DbtProject" />                               | A class that defines the representation of a dbt project and related settings that assist with managing dependencies and `manifest.json` preparation.                           |
| <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" />                     | A class that can be overridden to customize how Dagster asset metadata is derived from a dbt manifest.                                                                          |
| <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslatorSettings" />             | A class with settings to enable Dagster features for a dbt project.                                                                                                             |
| <PyObject section="libraries" module="dagster_dbt" object="DbtManifestAssetSelection" />                | A class that defines a selection of assets from a dbt manifest and a dbt selection string.                                                                                      |
| <PyObject section="libraries" module="dagster_dbt" object="build_dbt_asset_selection" />                | A helper method that builds a <PyObject section="libraries" module="dagster_dbt" object="DbtManifestAssetSelection" /> from a dbt manifest and dbt selection string.            |
| <PyObject section="libraries" module="dagster_dbt" object="build_schedule_from_dbt_selection" />        | A helper method that builds a <PyObject section="schedules-sensors" module="dagster" object="ScheduleDefinition" /> from a dbt manifest, dbt selection string, and cron string. |
| <PyObject section="libraries" module="dagster_dbt" object="get_asset_key_for_model" />                  | A helper method that retrieves the <PyObject section="assets" module="dagster" object="AssetKey" /> for a dbt model.                                                            |
| <PyObject section="libraries" module="dagster_dbt" object="get_asset_key_for_source" />                 | A helper method that retrieves the <PyObject section="assets" module="dagster" object="AssetKey" /> for a dbt source with a singular table.                                     |
| <PyObject section="libraries" module="dagster_dbt" object="get_asset_keys_by_output_name_for_source" /> | A helper method that retrieves the <PyObject section="assets" module="dagster" object="AssetKey" pluralize /> for a dbt source with multiple tables.                            |

## dbt models and Dagster asset definitions

Dagster’s [asset definitions](/guides/build/assets/) bear several similarities to dbt models. An asset definition contains an asset key, a set of upstream asset keys, and an operation that is responsible for computing the asset from its upstream dependencies. Models defined in a dbt project can be interpreted as Dagster asset definitions:

- The asset key for a dbt model is (by default) the name of the model.
- The upstream dependencies of a dbt model are defined with `ref` or `source` calls within the model's definition.
- The computation required to compute the asset from its upstream dependencies is the SQL within the model's definition.

These similarities make it natural to interact with dbt models as asset definitions. Let’s take a look at a dbt model and an asset definition, in code:

![Comparison of a dbt model and Dagster asset in code](/images/integrations/dbt/using-dbt-with-dagster/asset-dbt-model-comparison.png)

Here's what's happening in this example:

- The first code block is a **dbt model**
  - As dbt models are named using file names, this model is named `orders`
  - The data for this model comes from a dependency named `raw_orders`
- The second code block is a **Dagster asset**
  - The asset key corresponds to the name of the dbt model, `orders`
  - `raw_orders` is provided as an argument to the asset, defining it as a dependency

## Scaffolding a Dagster project from a dbt project

:::note

Check out [part two of the dbt & Dagster tutorial](/integrations/libraries/dbt/using-dbt-with-dagster/load-dbt-models) to see this concept in context.

:::

You can create a Dagster project that wraps your dbt project by using the [`dagster-dbt project scaffold`](/api/python-api/libraries/dagster-dbt#scaffold) command line interface.

```shell
dagster-dbt project scaffold --project-name project_dagster --dbt-project-dir path/to/dbt/project
```

This creates a directory called `project_dagster/` inside the current directory. The `project_dagster/` directory contains a set of files that define a Dagster project that loads the dbt project at the path defined by `--dbt-project-dir`. The path to the dbt project must contain a `dbt_project.yml`.

## Loading dbt models from a dbt project

:::note

Check out [part two of the dbt & Dagster tutorial](/integrations/libraries/dbt/using-dbt-with-dagster/load-dbt-models) to see this concept in context.

:::

The `dagster-dbt` library offers <PyObject section="libraries" module="dagster_dbt" object="dbt_assets" decorator /> to define Dagster assets for dbt models. It requires a [dbt manifest](https://docs.getdbt.com/reference/artifacts/manifest-json), or `manifest.json`, to be created from your dbt project to parse your dbt project's representation.

The manifest can be created in two ways:

1. **At run time**: A dbt manifest is generated when your Dagster definitions are loaded, or
2. **At build time**: A dbt manifest is generated before loading your Dagster definitions and is included as part of your Python package.

When deploying your Dagster project to production, **we recommend generating the manifest at build time** to avoid the overhead of recompiling your dbt project every time your Dagster code is executed. A `manifest.json` should be precompiled and included in the Python package for your Dagster code.

The easiest way to handle the creation of your manifest file is to use <PyObject section="libraries" object="DbtProject" module="dagster_dbt" />.

In the Dagster project created by the [`dagster-dbt project scaffold`](/api/python-api/libraries/dagster-dbt#scaffold) command, the creation of your manifest is handled at run time during development:

<CodeExample
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
  startAfter="start_compile_dbt_manifest_with_dbt_project"
  endBefore="end_compile_dbt_manifest_with_dbt_project"
/>

The manifest path can then be accessed with `my_dbt_project.manifest_path`.

When developing locally, you can run the following command to generate the manifest at run time for your dbt and Dagster project:

```shell
dagster dev
```

In production, a precompiled manifest should be used. Using <PyObject section="libraries" object="DbtProject" module="dagster_dbt" />, the manifest can be created at build time by running the [`dagster-dbt project prepare-and-package`](/api/python-api/libraries/dagster-dbt#prepare-and-package) command in your CI/CD workflow. For more information, see the [Deploying a Dagster project with a dbt project](#deploying-a-dagster-project-with-a-dbt-project) section.

## Deploying a Dagster project with a dbt project

:::note

**Got questions about our recommendations or something to add?**

Join our [GitHub discussion](https://github.com/dagster-io/dagster/discussions/13767) to share how you deploy your Dagster code with your dbt project.

:::

When deploying your Dagster project to production, your dbt project must be present alongside your Dagster project so that dbt commands can be executed. As a result, we recommend that you set up your continuous integration and continuous deployment (CI/CD) workflows to package the dbt project with your Dagster project.

### Deploying a dbt project from a separate git repository

If you are managing your Dagster project in a separate git repository from your dbt project, you should include the following steps in your CI/CD workflows.

In your CI/CD workflows for your Dagster project:

1. Include any secrets that are required by your dbt project in your CI/CD environment.
2. Clone the dbt project repository as a subdirectory of your Dagster project.
3. Run `dagster-dbt project prepare-and-package --file path/to/project.py` to
   - Build your dbt project's dependencies,
   - Create a dbt manifest for your Dagster project, and
   - Package your dbt project

In the CI/CD workflows for your dbt project, set up a dispatch action to trigger a deployment of your Dagster project when your dbt project changes.

### Deploying a dbt project from a monorepo

:::note

With [Dagster+](https://dagster.io/cloud), we streamline this option. As part of our Dagster+ onboarding for dbt users, we can automatically create a Dagster project in an existing dbt project repository.

:::

If you are managing your Dagster project in the same git repository as your dbt project, you should include the following steps in your CI/CD workflows.

In your CI/CD workflows for your Dagster and dbt project:

1. Include any secrets that are required by your dbt project in your CI/CD environment.
2. Run `dagster-dbt project prepare-and-package --file path/to/project.py` to
   - Build your dbt project's dependencies,
   - Create a dbt manifest for your Dagster project, and
   - Package your dbt project

## Leveraging dbt defer with branch deployments

:::note

This feature requires the `DAGSTER_BUILD_STATEDIR` environment variable to be set in your CI/CD. Learn more about required environment variables in CI/CD for Dagster+ [here](/dagster-plus/features/ci-cd/configuring-ci-cd).

:::

It is possible to leverage [dbt defer](https://docs.getdbt.com/reference/node-selection/defer) by passing a `state_path` to <PyObject section="libraries" object="DbtProject" module="dagster_dbt" />. This is useful for testing recent changes made in development against the state of the dbt project in production. Using `dbt defer`, you can run a subset of models or tests, those that have been changed between development and production, without having to build their upstream parents first.

In practice, this is most useful when combined with branch deployments in Dagster+, to test changes made in your branches. This can be done by updating your CI/CD files and your Dagster code.

First, let's take a look at your CI/CD files. You might have one or two CI/CD files to manage your production and branch deployments. In these files, find the steps related to your dbt project - refer to the [Deploying a Dagster project with a dbt project](#deploying-a-dagster-project-with-a-dbt-project) section for more information.

Once your dbt steps are located, add the following step to manage the state of your dbt project.

```bash
dagster-cloud ci dagster-dbt project manage-state --file path/to/project.py
```

The `dagster-cloud ci dagster-dbt project manage-state` CLI command fetches the `manifest.json` file from your production branch and saves it to a state directory, in order to power the `dbt defer` command.

In practice, this command fetches the `manifest.json` file from your production branch and add it to the state directory set to the `state_path` of the DbtProject found in `path/to/project.py`. The production `manifest.json` file can then be used as the deferred dbt artifacts.

Now that your CI/CD files are updated to manage the state of your dbt project using the dagster-cloud CLI, we need to update the Dagster code to pass a state directory to the DbtProject.

Update your Dagster code to pass a `state_path` to your `DbtProject` object. Note that value passed to `state_path` must be a path, relative to the dbt project directory, to a state directory of dbt artifacts. In the code below, we set the `state_path` to 'state/'. If this directory does not exist in your project structure, it will be created by Dagster.

Also, update the dbt command in your `@dbt_assets` definition to pass the defer args using `get_defer_args`.

<CodeExample
  startAfter="start_use_dbt_defer_with_dbt_project"
  endBefore="end_use_dbt_defer_with_dbt_project"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

## Using config with `@dbt_assets`

Similar to Dagster software-defined assets, `@dbt_assets` can use a config system to enable [run configuration](/guides/operate/configuration/run-configuration). This allows to provide parameters to jobs at the time they're executed.

In the context of dbt, this can be useful if you want to run commands or flags for specific use cases. For instance, you may want to add [the --full-refresh flag](https://docs.getdbt.com/reference/resource-configs/full_refresh) to your dbt commands in some cases. Using a config system, the `@dbt_assets` object can be easily modified to support this use case.

<CodeExample
  startAfter="start_config_dbt_assets"
  endBefore="end_config_dbt_assets"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

Now that the `@dbt_assets` object is updated, the run configuration can be passed to a job.

<CodeExample
  startAfter="start_config_dbt_job"
  endBefore="end_config_dbt_job"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

In the example above, the job is configured to use the `--full-refresh` flag with the dbt build command when materializing the assets.

## Scheduling dbt jobs

Once you have your dbt assets, you can define a job to materialize a selection of these assets on a schedule.

### Scheduling jobs that contain only dbt assets

In this example, we use the <PyObject section="libraries" module="dagster_dbt" object="build_schedule_from_dbt_selection" /> function to create a job, `daily_dbt_models`, as well as a schedule which will execute this job once a day. We define the set of models we'd like to execute using [dbt's selection syntax](https://docs.getdbt.com/reference/node-selection/syntax#how-does-selection-work), in this case selecting only the models with the tag `daily`.

<CodeExample
  startAfter="start_schedule_assets_dbt_only"
  endBefore="end_schedule_assets_dbt_only"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

### Scheduling jobs that contain dbt assets and non-dbt assets

In many cases, it's useful to be able to schedule dbt assets alongside non-dbt assets. In this example, we build an <PyObject section="assets" module="dagster" object="AssetSelection" /> of dbt assets using <PyObject section="libraries" module="dagster_dbt" object="build_dbt_asset_selection" />, then select all assets (dbt-related or not) which are downstream of these dbt models. From there, we create a job that targets that selection of assets and schedule it to run daily.

<CodeExample
  startAfter="start_schedule_assets_dbt_downstream"
  endBefore="end_schedule_assets_dbt_downstream"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

Refer to the [Schedule documentation](/guides/automate/schedules/) for more info on running jobs on a schedule.

## Understanding asset definition attributes

In Dagster, each asset definition has attributes. Dagster automatically generates these attributes for each asset definition loaded from the dbt project. These attributes can optionally be overridden by the user.

- [Customizing asset keys](#customizing-asset-keys)
- [Customizing group names](#customizing-group-names)
- [Customizing owners](#customizing-owners)
- [Customizing descriptions](#customizing-descriptions)
- [Customizing metadata](#customizing-metadata)
- [Customizing tags](#customizing-tags)
- [Customizing automation conditions](#customizing-automation-conditions)

### Customizing asset keys

For dbt models, seeds, and snapshots, the default asset key will be the configured schema for that node, concatenated with the name of the node.

| dbt node type         | Schema    | Model name   | Resulting asset key |
| --------------------- | --------- | ------------ | ------------------- |
| model, seed, snapshot | `None`    | `MODEL_NAME` | `MODEL_NAME`        |
|                       | `SCHEMA`  | `MODEL_NAME` | `SCHEMA/MODEL_NAME` |
|                       | `None`    | my_model     | some_model          |
|                       | marketing | my_model     | marketing/my_model  |

For dbt sources, the default asset key will be the name of the source concatenated with the name of the source table.

| dbt node type | Source name   | Table name   | Resulting asset key      |
| ------------- | ------------- | ------------ | ------------------------ |
| source        | `SOURCE_NAME` | `TABLE_NAME` | `SOURCE_NAME/TABLE_NAME` |
|               | jaffle_shop   | orders       | jaffle_shop/orders       |

There are two ways to customize the asset keys generated by Dagster for dbt assets:

1. Defining [meta config](https://docs.getdbt.com/reference/resource-configs/meta) on your dbt node, or
2. Overriding Dagster's asset key generation by implementing a custom <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" />.

To override an asset key generated by Dagster for a dbt node, you can define a `meta` key on your dbt node's `.yml` file. The following example overrides the asset key for a source and table as `snowflake/jaffle_shop/orders`:

```yaml
sources:
  - name: jaffle_shop
    tables:
      - name: orders
        meta:
          dagster:
            asset_key: ['snowflake', 'jaffle_shop', 'orders']
```

Alternatively, to override the asset key generation for all dbt nodes in your dbt project, you can create a custom <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" /> and implement <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator.get_asset_key" />. The following example adds a `snowflake` prefix to the default generated asset key:

<CodeExample
  startAfter="start_custom_asset_key_dagster_dbt_translator"
  endBefore="end_custom_asset_key_dagster_dbt_translator"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

### Customizing group names

For dbt models, seeds, and snapshots, the default Dagster group name will be the [dbt group](https://docs.getdbt.com/docs/build/groups) defined for that node.

| dbt node type         | dbt group name | Resulting Dagster group name |
| --------------------- | -------------- | ---------------------------- |
| model, seed, snapshot | `GROUP_NAME`   | `GROUP_NAME`                 |
|                       | `None`         | `None`                       |
|                       | finance        | finance                      |

There are two ways to customize the group names generated by Dagster for dbt assets:

1. Defining [meta config](https://docs.getdbt.com/reference/resource-configs/meta) on your dbt node, or
2. Overriding Dagster's group name generation by implementing a custom <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" />

To override the group name generated by Dagster for a dbt node, you can define a `meta` key in your dbt project file, on your dbt node's property file, or on the node's in-file config block. The following example overrides the Dagster group name for the following model as `marketing`:

```yaml
models:
  - name: customers
    config:
      meta:
        dagster:
          group: marketing
```

Alternatively, to override the Dagster group name generation for all dbt nodes in your dbt project, you can create a custom <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" /> and implement <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator.get_group_name" />. The following example defines `snowflake` as the group name for all dbt nodes:

<CodeExample
  startAfter="start_custom_group_name_dagster_dbt_translator"
  endBefore="end_custom_group_name_dagster_dbt_translator"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

### Customizing owners

For dbt models, seeds, and snapshots, the default Dagster owner will be the email associated with the [dbt group](https://docs.getdbt.com/docs/build/groups) defined for that node.

| dbt node type         | dbt group name | dbt group's email   | Resulting Dagster owner |
| --------------------- | -------------- | ------------------- | ----------------------- |
| model, seed, snapshot | `GROUP_NAME`   | `OWNER@DOMAIN.COM`  | `OWNER@DOMAIN.COM`      |
|                       | `GROUP_NAME`   | `None`              | `None`                  |
|                       | `None`         | `None`              | `None`                  |
|                       | finance        | `owner@company.com` | `owner@company.com`     |
|                       | finance        | `None`              | `None`                  |

There are two ways to customize the asset keys generated by Dagster for dbt assets:

1. Defining [meta config](https://docs.getdbt.com/reference/resource-configs/meta) on your dbt node, or
2. Overriding Dagster's generation of owners by implementing a custom <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" />

To override the owners generated by Dagster for a dbt node, you can define a `meta` key in your dbt project file, on your dbt node's property file, or on the node's in-file config block. The following example overrides the Dagster owners for the following model as `owner@company.com` and `team:data@company.com`:

```yaml
models:
  - name: customers
    config:
      meta:
        dagster:
          owners: ['owner@company.com', 'team:data@company.com']
```

Alternatively, to override the Dagster generation of owners for all dbt nodes in your dbt project, you can create a custom <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" /> and implement <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator.get_group_name" />. The following example defines `owner@company.com` and `team:data@company.com` as the owners for all dbt nodes:

<CodeExample
  startAfter="start_custom_owners_dagster_dbt_translator"
  endBefore="end_custom_owners_dagster_dbt_translator"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

### Customizing descriptions

For dbt models, seeds, and snapshots, the default Dagster description will be the dbt node's description.

To override the Dagster description for all dbt nodes in your dbt project, you can create a custom <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" /> and implement <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator.get_description" />. The following example defines the raw SQL of the dbt node as the Dagster description:

<CodeExample
  startAfter="start_custom_description_dagster_dbt_translator"
  endBefore="end_custom_description_dagster_dbt_translator"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

### Customizing metadata

For dbt models, seeds, and snapshots, the default Dagster definition metadata will be the dbt node's declared column schema.

To override the Dagster definition metadata for all dbt nodes in your dbt project, you can create a custom <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" /> and implement <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator.get_metadata"/>. The following example defines the metadata of the dbt node as the Dagster metadata, using <PyObject section="metadata" module="dagster" object="MetadataValue"/>:

<CodeExample
  startAfter="start_custom_metadata_dagster_dbt_translator"
  endBefore="end_custom_metadata_dagster_dbt_translator"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

Dagster also supports fetching additional metadata at dbt execution time to attach to asset materializations. For more information, see the [Customizing asset materialization metadata](#customizing-asset-materialization-metadata) section.

#### Attaching code reference metadata

Dagster's dbt integration can automatically attach [code reference](/guides/build/assets/metadata-and-tags/index.md#source-code) metadata to the SQL files backing your dbt assets. To enable this feature, set the `enable_code_references` parameter to `True` in the <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslatorSettings" /> passed to your <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" />:

<CodeExample path="docs_snippets/docs_snippets/guides/dagster/code_references/with_dbt_code_references.py" />

### Customizing tags

:::note

In Dagster, tags are key-value pairs. However, in dbt, tags are strings. To bridge this divide, the dbt tag string is used as the Dagster tag key, and the Dagster tag value is set to the empty string, `""`. Any dbt tags that don't match Dagster's supported tag key format (e.g. they contain unsupported characters) will be ignored by default.

:::

For dbt models, seeds, and snapshots, the default Dagster tags will be the dbt node's configured tags.

Any dbt tags that don't match Dagster's supported tag key format (e.g. they contain unsupported characters) will be ignored.

To override the Dagster tags for all dbt nodes in your dbt project, you can create a custom <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" /> and implement <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator.get_tags" />. The following converts dbt tags of the form `foo=bar` to key/value pairs:

<CodeExample
  startAfter="start_custom_tags_dagster_dbt_translator"
  endBefore="end_custom_tags_dagster_dbt_translator"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

### Customizing automation conditions

To override the <PyObject section="assets" module="dagster" object="AutomationCondition" /> generated for each dbt node in your dbt project, you can create a custom <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" /> and implement <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator.get_automation_condition" />. The following example defines <PyObject section="assets" object="AutomationCondition.eager" /> as the condition for all dbt nodes:

<CodeExample
  startAfter="start_custom_automation_condition_dagster_dbt_translator"
  endBefore="end_custom_automation_condition_dagster_dbt_translator"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

:::note

Ensure that the [`default_automation_condition_sensor` is enabled](/guides/automate/declarative-automation/#using-declarative-automation) for automation conditions to be evaluated.

:::

## dbt models, code versions, and "Unsynced"

Note that Dagster allows the optional specification of a [`code_version`](/guides/build/assets/defining-assets#asset-code-versions) for each asset definition, which are used to track changes. The `code_version` for an asset arising from a dbt model is defined automatically as the hash of the SQL defining the DBT model. This allows the asset graph in the UI to use the "Unsynced" status to indicate which dbt models have new SQL since they were last materialized.

## Loading dbt tests as asset checks

:::note

**Asset checks for dbt have been enabled by default, starting in `dagster-dbt` 0.23.0.**

`dbt-core` 1.6 or later is required for full functionality.

:::

Dagster loads your dbt tests as [asset checks](/guides/test/asset-checks).

### Indirect selection

Dagster uses [dbt indirect selection](https://docs.getdbt.com/reference/global-configs/indirect-selection) to select dbt tests. By default, Dagster won't set `DBT_INDIRECT_SELECTION` so that the set of tests selected by Dagster is the same as the selected by dbt. When required, Dagster will override `DBT_INDIRECT_SELECTION` to `empty` in order to explicitly select dbt tests. For example:

- Materializing dbt assets and excluding their asset checks
- Executing dbt asset checks without materializing their assets

### Singular tests

Dagster will load both generic and singular tests as asset checks. In the event that your singular test depends on multiple dbt models, you can use dbt metadata to specify which Dagster asset it should target. These fields can be filled in as they would be for the dbt [ref function](https://docs.getdbt.com/reference/dbt-jinja-functions/ref). The configuration can be supplied in a [config block](https://docs.getdbt.com/reference/data-test-configs) for the singular test.

```sql
{{
    config(
        meta={
            'dagster': {
                'ref': {
                    'name': 'customers',
                    'package_name': 'my_dbt_assets'
                    'version': 1,
                },
            }
        }
    )
}}
```

`dbt-core` version 1.6 or later is required for Dagster to read this metadata.

If this metadata isn't provided, Dagster won't ingest the test as an asset check. It will still run the test and emit a <PyObject section="assets" module="dagster" object="AssetObservation" /> events with the test results.

### Disabling asset checks

You can disable modeling your dbt tests as asset checks. The tests will still run and will be emitted as <PyObject section="assets" module="dagster" object="AssetObservation"/> events. To do so you'll need to define a <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslator" /> with <PyObject section="libraries" module="dagster_dbt" object="DagsterDbtTranslatorSettings" /> that have asset checks disabled. The following example disables asset checks when using <PyObject section="libraries" module="dagster_dbt" object="dbt_assets" decorator/>:

<CodeExample
  startAfter="start_disable_asset_check_dagster_dbt_translator"
  endBefore="end_disable_asset_check_dagster_dbt_translator"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

## Customizing asset materialization metadata

Dagster supports fetching additional metadata at dbt execution time to attach as [materialization metadata](/guides/build/assets/metadata-and-tags/), which is recorded each time your models are rebuilt and displayed in the Dagster UI.

### Fetching row count data

:::note

To use this feature, you'll need to be on at least `dagster>=0.17.6` and `dagster-dbt>=0.23.6`.

:::

Dagster can automatically fetch [row counts](/guides/build/assets/metadata-and-tags/) for dbt-generated tables and emit them as [materialization metadata](/guides/build/assets/metadata-and-tags/) to be displayed in the Dagster UI.

Row counts are fetched in parallel to the execution of your dbt models. To enable this feature, call <PyObject section="libraries" object="core.dbt_cli_invocation.DbtEventIterator.fetch_row_counts" module="dagster_dbt" displayText="fetch_row_counts()" /> on the <PyObject section="libraries" object="core.dbt_cli_invocation.DbtEventIterator" module="dagster_dbt" /> returned by the `stream()` dbt CLI call:

<CodeExample
  startAfter="start_fetch_row_count"
  endBefore="end_fetch_row_count"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

Once your dbt models have been materialized, you can view the row count data in the metadata table.

### Fetching column-level metadata

:::note

To use this feature, you'll need to be on at least `dagster>=1.8.0` and `dagster-dbt>=0.24.0`.

:::

Dagster allows you to emit column-level metadata, like [column schema](/guides/build/assets/metadata-and-tags/) and [column lineage](/guides/build/assets/metadata-and-tags/), as [materialization metadata](/guides/build/assets/metadata-and-tags/).

With this metadata, you can view documentation in Dagster for all columns, not just columns described in your dbt project.

Column-level metadata is fetched in parallel to the execution of your dbt models. To enable this feature, call <PyObject section="libraries" object="core.dbt_cli_invocation.DbtEventIterator.fetch_column_metadata" module="dagster_dbt" displayText="fetch_column_metadata()" /> on the <PyObject section="libraries" object="core.dbt_cli_invocation.DbtEventIterator" module="dagster_dbt" /> returned by the `stream()` dbt CLI call:

<CodeExample
  startAfter="start_fetch_column_metadata"
  endBefore="end_fetch_column_metadata"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

### Composing metadata fetching methods

Metadata fetching methods such as <PyObject section="libraries" object="core.dbt_cli_invocation.DbtEventIterator.fetch_column_metadata" module="dagster_dbt" displayText="fetch_column_metadata()" /> can be chained with other metadata fetching methods like <PyObject section="libraries" object="core.dbt_cli_invocation.DbtEventIterator.fetch_row_counts" module="dagster_dbt" displayText="fetch_row_counts()" />:

<CodeExample
  startAfter="start_fetch_column_metadata_chain"
  endBefore="end_fetch_column_metadata_chain"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

## Defining dependencies

- [Upstream dependencies](#upstream-dependencies)
- [Downstream dependencies](#downstream-dependencies)

### Upstream dependencies

#### Defining an asset as an upstream dependency of a dbt model

Dagster allows you to define existing assets as upstream dependencies of dbt models. For example, say you have the following asset with asset key `upstream`:

<CodeExample
  startAfter="start_upstream_dagster_asset"
  endBefore="end_upstream_dagster_asset"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

Then, in the downstream model, you can select from this source data. This defines a dependency relationship between your upstream asset and dbt model:

```sql
select *
  from {{ source("dagster", "upstream") }}
 where foo=1
```

#### Defining a dbt source as a Dagster asset

Dagster parses information about assets that are upstream of specific dbt models from the dbt project itself. Whenever a model is downstream of a [dbt source](https://docs.getdbt.com/docs/building-a-dbt-project/using-sources), that source will be parsed as an upstream asset.

For example, if you defined a source in your `sources.yml` file like this:

```yaml
sources:
  - name: jaffle_shop
    tables:
      - name: orders
```

and use it in a model:

```sql
select *
  from {{ source("jaffle_shop", "orders") }}
 where foo=1
```

Then this model has an upstream source with the `jaffle_shop/orders` asset key.

In order to manage this upstream asset with Dagster, you can define it by passing the key into an asset definition via <PyObject section="libraries" module="dagster_dbt" object="get_asset_key_for_source"/>:

<CodeExample
  startAfter="start_upstream_asset"
  endBefore="end_upstream_asset"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

This allows you to change asset keys within your dbt project without having to update the corresponding Dagster definitions.

The <PyObject section="libraries" module="dagster_dbt" object="get_asset_key_for_source" /> method is used when a source has only one table. However, if a source contains multiple tables, like this example:

```yaml
sources:
  - name: clients_data
    tables:
      - name: names
      - name: history
```

You can use define a <PyObject section="assets" module="dagster" object="multi_asset" decorator/> with keys from <PyObject section="libraries" module="dagster_dbt" object="get_asset_keys_by_output_name_for_source"/> instead:

<CodeExample
  startAfter="start_upstream_multi_asset"
  endBefore="end_upstream_multi_asset"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

### Downstream dependencies

Dagster allows you to define assets that are downstream of specific dbt models via <PyObject section="libraries" module="dagster_dbt" object="get_asset_key_for_model"/>. The below example defines `my_downstream_asset` as a downstream dependency of `my_dbt_model`:

<CodeExample
  startAfter="start_downstream_asset"
  endBefore="end_downstream_asset"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

In the downstream asset, you may want direct access to the contents of the dbt model. To do so, you can customize the code within your `@asset`-decorated function to load upstream data.

Dagster alternatively allows you to delegate loading data to an I/O manager. For example, if you wanted to consume a dbt model with the asset key `my_dbt_model` as a Pandas dataframe, that would look something like the following:

<CodeExample
  startAfter="start_downstream_asset_pandas_df_manager"
  endBefore="end_downstream_asset_pandas_df_manager"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

## Building incremental models using partitions

You can define a Dagster <PyObject section="partitions" module="dagster" object="PartitionsDefinition"/> alongside dbt in order to build incremental models.

Partitioned assets will be able to access the <PyObject section="partitions" module="dagster" object="TimeWindow"/>'s start and end dates, and these can be passed to dbt's CLI as variables which can be used to filter incremental models.

When a partition definition to passed to the <PyObject section="libraries" module="dagster_dbt" object="dbt_assets" decorator/> decorator, all assets are defined to operate on the same partitions. With this in mind, we can retrieve any time window from <PyObject section="execution" module="dagster"  object="AssetExecutionContext.partition_time_window" /> property in order to get the current start and end partitions.

<CodeExample
  startAfter="start_build_incremental_model"
  endBefore="end_build_incremental_model"
  path="docs_snippets/docs_snippets/integrations/dbt/dbt.py"
/>

With the variables defined, we can now reference `min_date` and `max_date` in our SQL and configure the dbt model as incremental. Here, we define an incremental run to operate on rows with `order_date` that is between our `min_date` and `max_date`.

```sql
-- Configure the model as incremental, use a unique_key and the delete+insert strategy to ensure the pipeline is idempotent.
{{ config(materialized='incremental', unique_key='order_date', incremental_strategy="delete+insert") }}

select * from {{ ref('my_model') }}

-- Use the Dagster partition variables to filter rows on an incremental run
{% if is_incremental() %}
where order_date >= '{{ var('min_date') }}' and order_date <= '{{ var('max_date') }}'
{% endif %}
```
