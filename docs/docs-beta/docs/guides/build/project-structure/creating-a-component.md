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

<CodeExample filePath="guides/components/shell-script-component/empty.py" language="python" />

This file contains the basic structure for the new component type. There are two methods that you'll need to implement:

- `get_schema`: This method should return a Pydantic model that defines the schema for the component. This is the schema for the data that goes into `component.yaml`.
- `load`: This method takes the loading context and returns an instance of the component class. This is where you'll load the parameters from the `component.yaml` file.
- `build_defs`: This method should return a `Definitions` object for this component.

## Defining a schema

The first step is to define a schema for the component. This means determining what aspects of the component should be customizable.

In this case, we'll want to define a few things:

- The path to the shell script that we'll want to run.
- The attributes of the asset that we expect this script to produce.
- Any tags or configuration related to the underlying compute.

To simplify common use cases, `dagster-components` provides schemas for common bits of configuration:

- `AssetAttributesModel`: This contains attributes that are common to all assets, such as the key, description, tags, and dependencies.
- `OpSpecModel`: This contains attributes specific to an underlying operation, such as the name and tags.

We can the schema for our component and add it to our class as follows:

<CodeExample filePath="guides/components/shell-script-component/with-config-schema.py" language="python" />

## Building definitions

Now that we've defined how the component is parameterized, we need to define how to turn those parameters into a `Definitions` object.

To do so, there are two methods that need to be overridden:

- `load`: This method is responsible for loading the configuration from the `component.yaml` file into the schema, from which it creates an instance of the component class.
- `build_defs`: This method is responsible for returning a `Definitions` object containing all definitions related to the component.

In our case, our `load` method will check the loaded parameters against our schema and then instantiate our class from those parameters.

Our `build_defs` method will create a single `@asset` that executes the provided shell script. By convention, we'll put the code to actually execute this asset inside of a function called `evaluate`. This makes it easier for future developers to create subclasses of this component.

<CodeExample filePath="guides/components/shell-script-component/with-build-defs.py" language="python" />

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

The components system supports a rich templating syntax that allows you to load arbitrary Python values based off of your `component.yaml` file.

When creating the schema for your component, you can specify custom output types that should be resolved at runtime. This allows you to expose complex object types, such as `PartitionsDefinition` or `AutomationCondition` to users of your component, even if they're working in pure YAML.

### Defining a resolvable field

When creating a schema for your component, if you have a field that should have some custom resolution logic, you can annotate that field with the `ResolvableFieldInfo` class. This allows you to specify:

- The output type of the field
- Any post-processing that should be done on the resolved value of that field
- Any additional scope that will be available to use when resolving that field

<CodeExample filePath="guides/components/shell-script-component/defining-resolvable-field.py" language="python" />

### Resolving fields

Once you've defined a resolvable field, you'll need to implement the logic to actually resolve it into the desired Python value.

The `ComponentSchemaBaseModel` class supports a `resolve_properties` method, which returns a dictionary of resolved properties for your component. This method accepts a `templated_value_resolver`, which holds any available scope that is available for use in the template.

If your resolvable field requires additional scope to be available, you can do so by using the `with_scope` method on the `templated_value_resolver`. This scope can be anything, such as a dictionary of properties related to an asset, or a function that returns a complex object type.

<CodeExample filePath="guides/components/shell-script-component/resolving-resolvable-field.py" language="python" />

The `ComponentSchemaBaseModel` class will ensure that the output type of the resolved field matches the type specified in the `ResolvableFieldInfo` annotation.

When a user instantiates a component, they will be able to use your custom scope in their `component.yaml` file:

```yaml
component_type: my_component

params:
  script_path: script.sh
  script_runner: "{{ get_script_runner('arg') }}"
```

## Next steps

- Add a new component to your project
