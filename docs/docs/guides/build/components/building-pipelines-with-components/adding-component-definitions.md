---
title: 'Adding Dagster Component definitions to your project'
sidebar_position: 200
description: Add Dagster components to your project with YAML using the dg scaffold defs command.
---

import DgScaffoldDefsTip from '@site/docs/partials/\_DgScaffoldDefsTip.md';

You can scaffold Dagster Component definitions in your project from the command line with the `dg scaffold defs` command, which will create a new directory inside your `defs/` folder that contains a `defs.yaml` file.

:::note Prerequisites

Before scaffolding a component definition, you must either [create a components-ready Dagster project](/guides/build/projects/creating-a-new-project) or [migrate an existing project to `dg`](/guides/build/projects/moving-to-components/migrating-project).

:::

## Viewing available components

You can view the available components in your environment by running the following command:

```bash
dg list components
```

If the component you want to use is not available in your environment, you will need to install it with `uv add` or `pip install`. For example, to install the dbt project component, you would run:

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-components-to-project/1-uv-add-dbt.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-components-to-project/1-pip-add-dbt.txt" />
  </TabItem>
</Tabs>

For more information on integrations available as Dagster components, see the [integrations documentation](/integrations/libraries).

### Viewing component documentation

To see automatically generated documentation for all components in your environment, you can run `dg dev` to start the webserver and navigate to the `Docs` tab for your project's code location:

<CliInvocationExample contents="dg dev" />

![Docs tab in Dagster webserver](/images/guides/labs/components/docs-in-UI.png)

## Scaffolding a component definition

Once you've decided on the component that you'd like to use, you can scaffold a definition for it by running `dg scaffold defs <component> <component-path>`. This will create a new directory inside your `defs/` folder that contains a `defs.yaml` file.

For example, to scaffold a dbt project component definition, you would run:

```
dg scaffold defs dagster_dbt.DbtProjectComponent jdbt --project-path dbt/jdbt
```

Some components may require different arguments to be passed on the command line, or generate additional files when scaffolded.

<DgScaffoldDefsTip />

### Python-formatted component definitions

To scaffold a component definition formatted in Python instead of YAML, you can use the `dg scaffold defs` command with the `--format python` option. For example, the following command will generate a `component.py` file for the dbt project component rather than a `defs.yaml` file:

```
dg scaffold defs dagster_dbt.DbtProjectComponent jdbt --project-path dbt/jdbt --format python
```

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/python-components/tree.txt" />

<CodeExample path="docs_snippets/docs_snippets/guides/components/python-components/python-component.py" title="component.py" language="python" />

## Configuration

### Basic configuration

`defs.yaml` is the primary configuration file for a component. It contains two top-level fields:

- `type`: The type of the component defined in this directory.
- `attributes`: A dictionary of attributes that are specific to this component. The schema for these attributes is defined by attributes on the `Component` and customized by overriding `get_model_cls` method on the component class.

To see a sample `defs.yaml` file for your specific component, you can [view the component documentation](#viewing-component-documentation) in the Docs tab of the Dagster UI.

### Component templating

Each `defs.yaml` file supports a rich templating syntax, powered by `jinja2`.

#### Templating environment variables

A common use case for templating is to avoid exposing environment variables (particularly secrets) in your YAML files. The Jinja scope for a `defs.yaml` file contains an `env` function that can be used to insert environment variables into the template:

<CodeExample path="docs_snippets/docs_snippets/guides/components/integrations/fivetran-component/9-customized-component.yaml" title="my_project/defs/fivetran_ingest/defs.yaml" language="yaml" />

#### Multiple component instances in the same file

To configure multiple instances of a component in the same `defs.yaml` file, add another block of YAML with top-level `type` and `attributes` keys, separated from the previous block by the `---` separator.


```yaml
type: snowflake_lib.SnowflakeComponent

attributes:
  account: "{{ env.SNOWFLAKE_INSTANCE_ONE_ACCOUNT }}"
  password: "{{ env.SNOWFLAKE_INSTANCE_ONE_PASSWORD }}"
---
type: snowflake_lib.SnowflakeComponent

attributes:
  account: "{{ env.SNOWFLAKE_INSTANCE_TWO_ACCOUNT }}"
  password: "{{ env.SNOWFLAKE_INSTANCE_TWO_PASSWORD }}"
```
