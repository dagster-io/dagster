---
title: "Adding components to your project"
sidebar_position: 200
---

:::info

This feature is still in development and might change in patch releases. It’s not production ready, and the documentation may also evolve. Stay tuned for updates.

:::

To add components to your project, you can instantiate them from the command line, which will create a new directory inside your `components/` folder that contains a `component.yaml` file.

If you want to use Python to add components to your project instead, see "[Adding components to your project with Python](adding-components-python)".

:::note Prerequisites

Before adding a component with Python, you must either [create a project with components](/guides/labs/components/building-pipelines-with-components/creating-a-code-location-with-components) or [migrate an existing code location to components](/guides/labs/components/migrating-to-components/migrating-code-location).

:::

## Finding a component

You can view the available component types in your environment by running the following command:

```bash
dg component-type list
```

This will display a list of all the component types that are available in your project. To see more information about a specific component type, you can run:

```bash
dg component-type docs <component-name>
```

This will display a webpage containing documentation for the specified component type.

## Instantiating a component

Once you've decided on the component type that you'd like to use, you can instantiate it by running:

```bash
dg component generate <component-type> <component-name>
```

This will create a new directory inside your `components/` folder that contains a `component.yaml` file. Some component types may also generate additional files as needed.

## Configuration

### Basic configuration

The `component.yaml` is the primary configuration file for a component. It contains two top-level fields:

- `type`: The type of the component defined in this directory
- `params`: A dictionary of parameters that are specific to this component type. The schema for these parameters is defined by the `get_schema` method on the component class.

To see a sample `component.yaml` file for your specific component, you can run:

```bash
dg component-type docs <component-name>
```

### Component templating

Each `component.yaml` file supports a rich templating syntax, powered by `jinja2`.

#### Templating environment variables

A common use case for templating is to avoid exposing environment variables (particularly secrets) in your YAML files. The Jinja scope for a `component.yaml` file contains an `env` function that can be used to insert environment variables into the template:

```yaml
component_type: my_snowflake_component

params:
    account: {{ env('SNOWFLAKE_ACCOUNT') }}
    password: {{ env('SNOWFLAKE_PASSWORD') }}
```
