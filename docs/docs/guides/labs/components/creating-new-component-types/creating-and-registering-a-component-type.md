---
title: 'Creating and registering a component type'
sidebar_position: 100
---

:::info

This feature is still in development and might change in patch releases. It’s not production ready, and the documentation may also evolve. Stay tuned for updates.

:::

The `dagster-components` system makes it easy to create new component types that can be reused across your project.

In most cases, component types map to a specific technology. For example, you might have a `DockerScriptComponent` that executes a script in a Docker container, or a `SnowflakeQueryComponent` that runs a query on Snowflake.

:::note

Refer to the project structuring guide to learn how to create a components-compatible project.

:::

## Scaffolding component type files

For this example, we'll write a lightweight component that executes a shell command.

First, we use the `dg` command-line utility to scaffold a new component type:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/1-dg-scaffold-shell-command.txt" />

This will add a new file to your project in the `lib` directory:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/2-shell-command-empty.py" language="python" title="my_component_library/lib/shell_command.py" />

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

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-config-schema.py" language="python" title="my_component_library/lib/shell_command.py"/>


## Defining the Python class

Next, we'll want to translate this schema into fully resolved Python objects. For example, our schema defines `asset_specs` as `Sequence[AssetSpecSchema]`, but at runtime we'll want to work with `Sequence[AssetSpec]`.

By convention, we'll use the `@dataclass` decorator to simplify our class definition. We can define attributes for our class that line up with the properties in our schema, but this time we'll use the fully resolved types where appropriate.

Our path will still just be a string, but our `asset_specs` will be a list of `AssetSpec` objects. `AssetSpecSchema` implements `ResolvableSchema[AssetSpec]`, which indicates that it can automatically resolve into an `AssetSpec` object, so we don't need to do any additional work to resolve this field for our component.



<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-class-defined.py" language="python" title="my_component_library/lib/shell_command.py"/>

:::tip

When defining a field on a component that isn't on the schema, or is of a different type, the components system allows you to provide custom resolution logic for that field. See the [Providing resolution logic for non-standard types](#advanced-providing-resolution-logic-for-non-standard-types) section for more information.
:::

## Building definitions

Now that we've defined how the component is parameterized, we need to define how to turn those parameters into a `Definitions` object.

To do so, we'll want to override the `build_defs` method, which is responsible for returning a `Definitions` object containing all definitions related to the component.

Our `build_defs` method will create a single `@asset` that executes the provided shell script. By convention, we'll put the code to actually execute this asset inside of a function called `execute`. This makes it easier for future developers to create subclasses of this component.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-build-defs.py" language="python" title="my_component_library/lib/shell_command.py" />

## Component registration

Following the steps above will automatically register your component type in your environment. You can now run:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/3-dg-list-component-types.txt" />

and see your new component type in the list of available component types.

You can also view automatically generated documentation describing your new component type by running:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/4-dg-component-type-docs.txt" />

![](/images/guides/build/projects-and-components/components/component-type-docs.png)


Now, you can use this component type to create new component instances.

## Configuring custom scaffolding

Once your component type is registered, instances of the component type can be scaffolded using the `dg scaffold component` command:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/6-scaffold-instance-of-component.txt" />

By default, this will create a new directory alongside an unpopulated `component.yaml` file. However, you can customize this behavior by decorating your component_type with `scaffoldable`.

In this case, we might want to scaffold a template shell script alongside a filled-out `component.yaml` file, which we accomplish with a custom scaffolder:

<CodeExample  path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-scaffolder.py" language="python" title="my_component_library/lib/shell_command.py"/>

Now, when we run `dg scaffold component`, we'll see that a template shell script is created alongside a filled-out `component.yaml` file:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/7-scaffolded-component.yaml" language="yaml" title="my_component_library/components/my_shell_command/component.yaml" />

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/8-scaffolded-component-script.sh" language="bash" title="my_component_library/components/my_shell_command/script.sh" />

## [Advanced] Providing resolution logic for non-standard types

In most cases, the types you use in your component schema and in the component class will be the same, or will have out-of-the-box resolution logic, as in the case of `AssetSpecSchema` and `AssetSpec`.

However, in some cases you may want to use a type that doesn't have an existing schema equivalent.  In this case, you can provide a function that will resolve the value to the desired type by providing an annotation on the field with `Annotated[<type>, FieldResolver(...)]`.

For example, we might want to provide an API client to our component, which can be configured with an API key in YAML, or a mock client in tests:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/custom-schema-resolution.py" language="python" />

## [Advanced] Customize rendering of YAML values

The components system supports a rich templating syntax that allows you to load arbitrary Python values based off of your `component.yaml` file. All string values in a `ResolvableModel` can be templated using the Jinja2 templating engine, and may be resolved into arbitrary Python types. This allows you to expose complex object types, such as `PartitionsDefinition` or `AutomationCondition` to users of your component, even if they're working in pure YAML.

You can define custom values that will be made available to the templating engine by defining a `get_additional_scope` classmethod on your component. In our case, we can define a `"daily_partitions"` function which returns a `DailyPartitionsDefinition` object with a pre-defined start date:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/shell-script-component/with-custom-scope.py" language="python" />

When a user instantiates this component, they will be able to use this custom scope in their `component.yaml` file:

```yaml
component_type: my_component

attributes:
  script_path: script.sh
  asset_specs:
    - key: a
      partitions_def: "{{ daily_partitions }}"
```

## Next steps

- [Add a new component to your project](/guides/labs/components/building-pipelines-with-components/adding-components)
