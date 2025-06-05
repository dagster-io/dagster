---
title: 'Adding components to your project with YAML'
sidebar_position: 200
description: Add Dagster components to your project with YAML using the dg scaffold defs command.
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

To add components to your project, you can scaffold them from the command line, which will create a new directory inside your `defs/` folder that contains a `defs.yaml` file.

If you want to use Python to add components to your project instead, see "[Adding components to your project with Python](/guides/labs/components/building-pipelines-with-components/adding-components-python)".

:::note Prerequisites

Before adding a component, you must either [create a Dagster project with components](/guides/labs/components/building-pipelines-with-components/creating-a-project-with-components) or [migrate an existing project to `dg`](/guides/labs/dg/incrementally-adopting-dg/migrating-project).

:::

## Finding a component

You can view the available components in your environment by running the following command:

```bash
dg list components
```

:::note

If the component you want to use is not available in your environment, you will need to install it with `uv add` or `pip install`. For example, to install the dbt project component, you would run:

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-components-to-project/1-uv-add-dbt.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/adding-components-to-project/1-pip-add-dbt.txt" />
  </TabItem>
</Tabs>

:::

To see more information about a specific component, you can run:

```bash
dg docs serve
```

This will display a webpage containing documentation for the components.

## Scaffolding a component

Once you've decided on the component that you'd like to use, you can scaffold a definition for it by running:

```bash
dg scaffold defs <component> <component-path>
```

This will create a new directory inside your `defs/` folder that contains a `defs.yaml` file. Some components may require different arguments to be passed on the command line, or generate additional files as needed.

## Configuration

### Basic configuration

The `defs.yaml` is the primary configuration file for a component. It contains two top-level fields:

- `type`: The type of the component defined in this directory
- `attributes`: A dictionary of attributes that are specific to this component. The schema for these attributes is defined by attributes on the `Component` and totally customized by overriding `get_model_cls` method on the component class.

To see a sample `defs.yaml` file for your specific component, you can run:

```bash
dg docs serve
```

### Component templating

Each `defs.yaml` file supports a rich templating syntax, powered by `jinja2`.

#### Templating environment variables

A common use case for templating is to avoid exposing environment variables (particularly secrets) in your YAML files. The Jinja scope for a `defs.yaml` file contains an `env` function that can be used to insert environment variables into the template:

```yaml
type: snowflake_lib.SnowflakeComponent

attributes:
  account: "{{ env('SNOWFLAKE_ACCOUNT') }}"
  password: "{{ env('SNOWFLAKE_PASSWORD') }}"
```

#### Multiple component instances in the same file

To configure multiple instances of a component in the same `defs.yaml` file, add another block of YAML with top-level `type` and `attributes` keys, separated from the previous block by the `---` separator.


```yaml
type: snowflake_lib.SnowflakeComponent

attributes:
  account: "{{ env('SNOWFLAKE_INSTANCE_ONE_ACCOUNT') }}"
  password: "{{ env('SNOWFLAKE_INSTANCE_ONE_PASSWORD') }}"
---
type: snowflake_lib.SnowflakeComponent

attributes:
  account: "{{ env('SNOWFLAKE_INSTANCE_TWO_ACCOUNT') }}"
  password: "{{ env('SNOWFLAKE_INSTANCE_TWO_PASSWORD') }}"
```
