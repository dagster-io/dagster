---
title: 'Creating and registering a component type'
sidebar_position: 100
---

:::info

This feature is still in development and might change in patch releases. It’s not production ready, and the documentation may also evolve. Stay tuned for updates.

:::

The `dagster-components` system makes it easy to create new component types that can be reused across your project.

In most cases, component types map to a specific technology. For example, you might have a `DockerScriptComponent` that executes a script in a Docker container, or a `SnowflakeQueryComponent` that runs a query on Snowflake.

:::note Prerequisites

Before following the steps in this article, you must create a [components-compatible code location](/guides/labs/components/building-pipelines-with-components/creating-a-code-location-with-components).

:::

## 1. Scaffold a new component type

For this example, we'll write a lightweight component that executes a shell command.

First, use the `dg` command line utility to scaffold a new component type:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/1-dg-scaffold-shell-command.txt" />

This will add a new file to the project in the `lib` directory:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/2-shell-command-empty.py" language="python" title="my_component_library/lib/shell_command.py" />

This file contains the basic structure for the new component type. There are two methods that we'll need to implement:

- `get_schema`: This method should return a Pydantic model that defines the schema for the component. This is the schema for the data that goes into `component.yaml`.
- `build_defs`: This method should return a `Definitions` object for this component.

## 2. Define a schema

Next, we'll define a schema for our component. This means determining what aspects of the component should be customizable.

In this case, we will define the following:

- The path to the shell script that you want to run
- The assets that you expect this script to produce

You can define the schema for your component and add it to your class as follows:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-config-schema.py" language="python" />

:::tip

To simplify common use cases, `dagster-components` provides schemas for common bits of configuration, such as `AssetSpecSchema`, which contains attributes that are common to all assets, such as the key, description, tags, and dependencies.

:::

## 3. Define the Python class

Next, we'll need to translate this schema into fully-resolved Python objects. For example, the schema defines `asset_specs` as `Sequence[AssetSpecSchema]`, but at runtime, we'll want to work with `Sequence[AssetSpec]`.

By convention, we'll use the `@dataclass` decorator to simplify our class definition. We can define attributes for our class that line up with the properties in our schema, but this time, we'll use the fully-resolved types where appropriate.

Our path will still just be a string, but our `asset_specs` will be a list of `AssetSpec` objects. Whenever we define a field on the component that isn't on the schema, or is a different type, we can add an annotation to that field with `Annotated[<type>, FieldResolver(...)]` to tell the system how to resolve that particular field.

In our case, we'll just define a single field resolver for the `asset_specs` field on our component. Because `AssetSpecSchema` is a `ResolvableModel`, this can be directly resolved into an `AssetSpec` object using `context.resolve_value()`:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-class-defined.py" language="python" />

## 4. Build definitions

Now that we've defined how the component is parameterized, we need to define how to turn those parameters into a `Definitions` object.

To do so, we'll override the `build_defs` method, which is responsible for returning a `Definitions` object containing all definitions related to the component.

Our `build_defs` method will create a single `@asset` that executes the provided shell script. By convention, we'll put the code to actually execute this asset inside of a function called `execute`. This makes it easier for future developers to create subclasses of this component:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-build-defs.py" language="python" />

## 5. Register the component type

Following the steps above will automatically register the component type in your environment. You can now run the following command to see your new component type in the list of available component types:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/3-dg-list-component-types.txt" />

You can also view automatically generated documentation for your new component type by running:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/4-dg-component-type-docs.txt" />

![](/images/guides/build/projects-and-components/components/component-type-docs.png)

## Custom templating

The components system supports a rich templating syntax that allows you to load arbitrary Python values based off of your `component.yaml` file. All string values in a `ResolvableModel` can be templated using the [Jinja2 templating engine](https://jinja.palletsprojects.com/en/stable/), and may be resolved into arbitrary Python types. This allows you to expose complex object types, such as `PartitionsDefinition` or `AutomationCondition` to users of your component, even if they're working in pure YAML.

You can define custom values that will be made available to the templating engine by defining a `get_additional_scope` class method on your component. In our case, we can define a `"daily_partitions"` function which returns a `DailyPartitionsDefinition` object with a pre-defined start date:

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
