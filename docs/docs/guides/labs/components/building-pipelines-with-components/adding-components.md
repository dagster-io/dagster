---
title: 'Adding components to your project with YAML'
sidebar_position: 200
description: Add Dagster components to your project with YAML using the dg scaffold command.
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

To add components to your project, you can instantiate them from the command line, which will create a new directory inside your `components/` folder that contains a `component.yaml` file.

If you want to use Python to add components to your project instead, see "[Adding components to your project with Python](/guides/labs/components/building-pipelines-with-components/adding-components-python)".

:::note Prerequisites

Before adding a component, you must either [create a project with components](/guides/labs/components/building-pipelines-with-components/creating-a-project-with-components) or [migrate an existing project to `dg`](/guides/labs/dg/incrementally-adopting-dg/migrating-project).

:::

## Finding a component

You can view the available component types in your environment by running the following command:

```bash
dg list plugins --feature component
```

This will display a list of all the component types that are available in your project. To see more information about a specific component type, you can run:

```bash
dg docs serve
```

This will display a webpage containing documentation for the specified component type.

## Instantiating a component

Once you've decided on the component type that you'd like to use, you can instantiate it by running:

```bash
dg scaffold <component-type> <component-path>
```

This will create a new directory inside your `defs/` folder that contains a `component.yaml` file. Some component types may also generate additional files as needed.

## Configuration

### Basic configuration

The `component.yaml` is the primary configuration file for a component. It contains two top-level fields:

- `type`: The type of the component defined in this directory
- `attributes`: A dictionary of attributes that are specific to this component type. The schema for these attributes is defined by attributes on the `Component` and totally customized by overriding `get_model_cls` method on the component class.

To see a sample `component.yaml` file for your specific component, you can run:

```bash
dg docs serve
```

### Component templating

Each `component.yaml` file supports a rich templating syntax, powered by `jinja2`.

#### Templating environment variables

A common use case for templating is to avoid exposing environment variables (particularly secrets) in your YAML files. The Jinja scope for a `component.yaml` file contains an `env` function that can be used to insert environment variables into the template:

```yaml
component_type: my_snowflake_component

attributes:
  account: "{{ env('SNOWFLAKE_ACCOUNT') }}"
  password: "{{ env('SNOWFLAKE_PASSWORD') }}"
```
