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
- `load`: This method takes the loading context and returns an instance of the component class. This is where you'll load the parameters from the `component.yaml` file.
- `build_defs`: This method should return a `Definitions` object for this component.

## Defining a schema

The first step is to define a schema for the component. This means determining what aspects of the component should be customizable.

In this case, we'll want to define a few things:

- The path to the shell script that we'll want to run.
- The specs of the assets that we expect this script to produce.
- Any tags or configuration related to the underlying compute.

The user will be able to specify these parameters in the relevant `component.yaml` file to configure this component.

To simplify common use cases, `dagster-components` provides schemas for common bits of configuration:

- `AssetSpecSchema`: This contains attributes that are common to all assets, such as the key, description, tags, and dependencies.
- `OpSpecSchema`: This contains attributes specific to an underlying operation, such as the name and tags.

We can create the schema for our component and add it to our class as follows:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-config-schema.py" language="python" />

Because the argument names in the schema match the names of the arguments in the `ShellCommandComponent` class, the `load` method will automatically populate the class with the values from the schema, and will automatically resolve the `AssetSpecSchema`s into `AssetSpec` objects.

## Building definitions

Now that we've defined how the component is parameterized, we need to define how to turn those parameters into a `Definitions` object.

To do so, we'll want to override the `build_defs` method, which is responsible for returning a `Definitions` object containing all definitions related to the component.

Our `build_defs` method will create a single `@multi_asset` that executes the provided shell script. By convention, we'll put the code to actually execute this asset inside of a function called `execute`. This makes it easier for future developers to create subclasses of this component.

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



## Next steps

- Add a new component to your project
