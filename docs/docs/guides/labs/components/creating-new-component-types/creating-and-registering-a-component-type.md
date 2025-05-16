---
description: Create and register reusable component types with the dg CLI.
sidebar_position: 100
title: Creating and registering a component type
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

The components system makes it easy to create new component types that you and your teammates can reuse across your Dagster project.

In most cases, component types map to a specific technology. For example, you might create a `DockerScriptComponent` that executes a script in a Docker container, or a `SnowflakeQueryComponent` that runs a query on Snowflake.

## Prerequisites

Before creating and registering custom component types, you will need to [create a components-ready project](/guides/labs/dg/creating-a-project).

## Creating a new component type

For this example, we'll create a `ShellCommand` component type that executes a shell command.

### 1. Create the new component type file

First, use the `dg scaffold component-type` command to scaffold the `ShellCommand` component type:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/1-dg-scaffold-shell-command.txt" />

This will add a new file to the `lib` directory of your Dagster project that contains the basic structure for the new component type:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/2-shell-command-empty.py"
  language="python"
  title="my_component_library/lib/shell_command.py"
/>

:::tip

`Model` is used to implement a YAML interface for a component type. If your component type only needs a Pythonic interface, you can use the `--no-model` flag when creating it:

```
dg scaffold component-type ShellCommand --no-model
```

This will allow you to implement an `__init__` method for your class, either manually or by using `@dataclasses.dataclass`.

:::

### 2. Update the component type Python class

The next step is to define the information the component type needs when it is instantiated.

The `ShellCommand` component type will need the following to be defined:

- The path to the shell script to be run
- The assets the shell script is expected to produce

The `ShellCommand` class inherits from <PyObject section="resolved" module="dagster.components" object="Resolvable" />, in addition to <PyObject section="components" module="dagster.components" object="Component" />. `Resolvable` handles deriving a YAML schema for the `ShellCommand` class based on what the class is annotated with. To simplify common use cases, Dagster provides annotations for common bits of configuration, such as `ResolvedAssetSpec`, which will handle exposing a schema for defining <PyObject section="assets" module="dagster" object="AssetSpec" pluralize /> from YAML and resolving them before instantiating the component.

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

When defining a field on a component that isn't on the schema, or is of a different type, the components system allows you to provide custom resolution logic for that field. For more information, see "[Providing resolution logic for non-standard types](/guides/labs/components/creating-new-component-types/component-type-customization#providing-resolution-logic-for-non-standard-types)".

:::

### 3. Update the `build_defs` method

Next, you'll need to define how to turn the component parameters into a `Definitions` object.

To do so, you will need to update the `build_defs` method, which is responsible for returning a `Definitions` object containing all definitions related to the component.

In this example, the `build_defs` method creates a single `@asset` that executes the provided shell script. By convention, the code to execute this asset is placed inside of a function called `execute`, which will make it easier for future developers to create subclasses of this component:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-build-defs.py"
  language="python"
  title="my_component_library/lib/shell_command.py"
/>

## Registering a new component type

Following the steps above will automatically register your component type in your environment. To see your new component type in the list of available component types, run `dg list plugins`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/3-dg-list-plugins.txt" />

You can also view automatically generated documentation describing your new component type by running `dg docs serve`:

<CliInvocationExample contents="dg docs serve" />

## Instantiating the new component type in your project

After you register your new component type, you can instantiate and use the component in your Dagster project with the `dg scaffold` command:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/4-scaffold-instance-of-component.txt" />
