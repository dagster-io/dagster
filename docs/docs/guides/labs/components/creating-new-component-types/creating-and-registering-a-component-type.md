---
description: Create and register reusable Dagster component types with the dg CLI.
sidebar_position: 100
title: Creating and registering a component type
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

The components system makes it easy to create new component types that can be reused across your project.

In most cases, component types map to a specific technology. For example, you might have a `DockerScriptComponent` that executes a script in a Docker container, or a `SnowflakeQueryComponent` that runs a query on Snowflake.

:::note

Refer to the project structuring guide to learn how to create a components-compatible project.

:::

## Scaffolding component type files

For this example, we'll write a lightweight component that executes a shell command.

First, we use the `dg` command-line utility to scaffold a new component type:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/1-dg-scaffold-shell-command.txt" />

This will add a new file to your project in the `lib` directory:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/2-shell-command-empty.py"
  language="python"
  title="my_component_library/lib/shell_command.py"
/>

This file contains the basic structure for the new component type. Our goal is to implement the `build_defs` method to return a `Definitions`. This will require some input which we will define as what our component class is instantiated with.

:::note
The use of `Model` is optional if you only want a Pythonic interface to the component. If you wish to implement an `__init__` method for your class (manually or using `@dataclasses.dataclass`), you can provide the `--no-model` flag to the `dg scaffold` command.
:::

## Defining the Python class

The first step is to define what information this component needs. This means determining what aspects of the component should be customizable.

In this case, we'll want to define a few things:

- The path to the shell script that we'll want to run.
- The assets that we expect this script to produce.

Our class inherits from `Resolvable` in addition to `Component`. This will handle deriving a yaml schema for our class based on what the class is annotated with. To simplify common use cases, Dagster provides annotations for common bits of configuration, such as `ResolvedAssetSpec`, which will handle exposing a schema for defining `AssetSpec`s from yaml and resolving them before instantiating our component.

We can define the schema for our component and add it to our class as follows:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-config-schema.py"
  language="python"
  title="my_component_library/lib/shell_command.py"
  />

Additionally, it's possible to include metadata for your Component by overriding the `get_component_type_metadata` method. This allows you to set fields like `owners` and `tags` that will be visible in the generated documentation.

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-config-schema-meta.py"
  language="python"
  title="my_component_library/lib/shell_command.py"
  />

:::tip

When defining a field on a component that isn't on the schema, or is of a different type, the components system allows you to provide custom resolution logic for that field. See the [Providing resolution logic for non-standard types](#advanced-providing-resolution-logic-for-non-standard-types) section for more information.
:::

## Building definitions

Now that we've defined how the component is parameterized, we need to define how to turn those parameters into a `Definitions` object.

To do so, we'll want to override the `build_defs` method, which is responsible for returning a `Definitions` object containing all definitions related to the component.

Our `build_defs` method will create a single `@asset` that executes the provided shell script. By convention, we'll put the code to actually execute this asset inside of a function called `execute`. This makes it easier for future developers to create subclasses of this component.

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-build-defs.py"
  language="python"
  title="my_component_library/lib/shell_command.py"
/>

## Component registration

Following the steps above will automatically register your component type in your environment. You can now run:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/3-dg-list-plugins.txt" />

and see your new component type in the list of available component types.

You can also view automatically generated documentation describing your new component type by running:

<CliInvocationExample contents="dg docs serve" />

Now, you can use this component type to create new component instances.

## Next steps

- [Add a new component to your project](/guides/labs/components/building-pipelines-with-components/adding-components)