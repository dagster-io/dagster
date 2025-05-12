---
description: Create and register reusable Dagster component types with the dg CLI.
sidebar_position: 100
title: Creating and registering a component type
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

The components system makes it easy to create new component types that can be reused across your project.

In most cases, component types map to a specific technology. For example, you might have a `DockerScriptComponent` that executes a script in a Docker container, or a `SnowflakeQueryComponent` that runs a query on Snowflake.

## Prerequisites

Before creating and registering custom component types, you will need to [create a components-ready project](/guides/labs/dg/creating-a-project).

## Creating a new component type

For this example, we'll create a component type that executes a shell command.

### 1. Create the new component type file

First, use the `dg scaffold component-type` command to create a new component type:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/1-dg-scaffold-shell-command.txt" />

This will add a new file to your project in the `lib` directory:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/2-shell-command-empty.py"
  language="python"
  title="my_component_library/lib/shell_command.py"
/>

This file contains the basic structure for the new component type. Our goal is to implement the `build_defs` method to return a `Definitions` object. This will require some input, which you will define as what your component class is instantiated with.

:::note

The use of `Model` is optional if you only want a Pythonic interface to the component. If you wish to implement an `__init__` method for your class (manually or using `@dataclasses.dataclass`), you can provide the `--no-model` flag to the `dg scaffold` command.

:::

### 2. Define the component type Python class

The next step is to define what information this component needs. This means determining what aspects of the component should be customizable.

The `ShellCommand` component type will need the following to be defined:

- The path to the shell script to be run
- The assets the shell script is expected to produce

The `ShellCommand` class inherits from <PyObject section="resolved" module="dagster" object="Resolvable" />, in addition to <PyObject section="resolved" module="dagster" object="Component" />. `Resolvable` handles deriving a YAML schema for the `ShellCommand` class based on what the class is annotated with. To simplify common use cases, Dagster provides annotations for common bits of configuration, such as `ResolvedAssetSpec`, which will handle exposing a schema for defining <PyObject section="assets" module="dagster" object="AssetSpec" pluralize /> from YAML and resolving them before instantiating the component.

You can define the schema for the `ShellCommand` component and add it to the `ShellCommand` class as follows:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-config-schema.py"
  language="python"
  title="my_component_library/lib/shell_command.py"
  />

Additionally, you can include metadata for your component by overriding the `get_spec` method. This allows you to set fields like `owners` and `tags` that will be visible in the generated documentation:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-config-schema-meta.py"
  language="python"
  title="my_component_library/lib/shell_command.py"
  />

:::tip

When defining a field on a component that isn't on the schema, or is of a different type, the components system allows you to provide custom resolution logic for that field. For more information, see "[Providing resolution logic for non-standard types](/guides/labs/components/creating-new-component-types/configuring-custom-scaffolding#advanced-providing-resolution-logic-for-non-standard-types)".

:::

### 3. Build definitions

Now that we've defined how the component is parameterized, we need to define how to turn those parameters into a `Definitions` object.

To do so, we'll want to override the `build_defs` method, which is responsible for returning a `Definitions` object containing all definitions related to the component.

Our `build_defs` method will create a single `@asset` that executes the provided shell script. By convention, we'll put the code to actually execute this asset inside of a function called `execute`. This makes it easier for future developers to create subclasses of this component.

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-build-defs.py"
  language="python"
  title="my_component_library/lib/shell_command.py"
/>

## Registering a new component type

Following the steps above will automatically register your component type in your environment. You can now run:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/3-dg-list-plugins.txt" />

and see your new component type in the list of available component types.

You can also view automatically generated documentation describing your new component type by running:

<CliInvocationExample contents="dg docs serve" />

## Adding instances of the new component type to your project

After you register your new component type, you and your teammates can add instances of the component to your project with the `dg scaffold` command:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/4-scaffold-instance-of-component.txt" />
