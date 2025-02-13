---
title: 'Creating a New Component Type'
sidebar_position: 100
---

:::note
Refer to the project structuring guide to learn how to create a components-compatible project.
:::

The `dagster-components` system makes it easy to create new component types that can be reused across your project.

In most cases, component types map to a specific technology. For example, you might have a `DockerScriptComponent` that executes a script in a Docker container, or a `SnowflakeQueryComponent` that runs a query on Snowflake.

## Making a component library

To let the `dg` cli know that your Python package contains component types, you'll want to update your `pyproject.toml` file with the following configuration:

```toml
[tool.dg]
is_component_lib = true
```

By default, it is assumed that all components types will be defined in `your_package.lib`. If you'd like to define your components in a different directory, you can specify this in your `pyproject.toml` file:

```toml
[tool.dg]
is_component_lib = true
component_lib_package="your_package.other_module"
```

Once this is done, as long as this package is installed in your environment, you'll be able to use the `dg` command-line utility to interact with your component types.

## Scaffolding a new component type

For this example, we'll write a lightweight component that executes a shell command.

First, we use the `dg` command-line utility to scaffold a new component type:

```bash
dg component-type generate shell_command
```

This will add a new file to your project in the `lib` directory:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/empty.py" language="python" />

This file contains the basic structure for the new component type. There are two methods that you'll need to implement:

- `get_schema`: This method should return a Pydantic model that defines the schema for the component. This is the schema for the data that goes into `component.yaml`.
- `build_defs`: This method should return a `Definitions` object for this component.

## Defining a schema

The first step is to define a schema for the component. This means determining what aspects of the component should be customizable.

In this case, we'll want to define a few things:

- The path to the shell script that we'll want to run.
- The assets that we expect this script to produce.

To simplify common use cases, `dagster-components` provides schemas for common bits of configuration, such as `AssetSpecSchema`, which contains attributes that are common to all assets, such as the key, description, tags, and dependencies.

We can the schema for our component and add it to our class as follows:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-config-schema.py" language="python" />


## Defining the python class

Next, we'll want to translate this schema into fully-resolved python objects. For example, our schema defines `asset_specs` as `Sequence[AssetSpecSchema]`, but at runtime we'll want to work with `Sequence[AssetSpec]`.

By convention, we'll use the `@dataclass` decorator to simplify our class definition. We can define attributes for our class that line up with the properties in our schema, but this time we'll use the fully-resolved types where appropriate.

Our path will still just be a string, but our `asset_specs` will be a list of `AssetSpec` objects. Whenever we define a field on the component that isn't on the schema, or is a different type, we can define an `@field_resolver` to tell the system how to resolve that particular field.

In our case, we'll just define a single field resolver for the `asset_specs` field on our component.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-class-defined.py" language="python" />


## Building definitions

Now that we've defined how the component is parameterized, we need to define how to turn those parameters into a `Definitions` object.

To do so, we'll want to override the `build_defs` method, which is responsible for returning a `Definitions` object containing all definitions related to the component.

Our `build_defs` method will create a single `@asset` that executes the provided shell script. By convention, we'll put the code to actually execute this asset inside of a function called `execute`. This makes it easier for future developers to create subclasses of this component.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-build-defs.py" language="python" />

## Component registration

Following the steps above will automatically register your component type in your environment. You can now run:

```bash
dg component-type list
```

and see your new component type in the list of available component types.

You can also view automatically generated documentation describing your new component type by running:

```bash
dg component-type docs your_library.shell_command
```

## [Advanced] Custom templating

The components system supports a rich templating syntax that allows you to load arbitrary Python values based off of your `component.yaml` file. All string values in a `ResolvableModel` can be templated using the Jinja2 templating engine, and may be resolved into arbitrary Python types. This allows you to expose complex object types, such as `PartitionsDefinition` or `AutomationCondition` to users of your component, even if they're working in pure YAML.

You can define custom values that will be made available to the templating engine by defining a `get_additional_scope` classmethod on your component. In our case, we can define a `"daily_partitions"` function which returns a `DailyPartitionsDefinition` object with a pre-defined start date:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-custom-scope.py" language="python" />

When a user instantiates this component, they will be able to use this custom scope in their `component.yaml` file:

```yaml
component_type: my_component

params:
  script_path: script.sh
  asset_specs:
    - key: a
      partitions_def: "{{ daily_partitions }}"
```

## Next steps

- Add a new component to your project
