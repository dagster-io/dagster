---
description: Use the dg CLI to create and register a reusable component with a YAML or Pythonic interface.
sidebar_position: 100
title: Creating and registering a component
---

The components system makes it easy to create new components that you and your teammates can reuse across your Dagster project.

In most cases, components map to a specific technology. For example, you might create a `DockerScriptComponent` that executes a script in a Docker container, or a `SnowflakeQueryComponent` that runs a query on Snowflake.

:::info Prerequisites

Before creating and registering custom components, you will need to [create a components-ready project](/guides/build/projects/creating-a-new-project).

:::

## Creating a new component

For this example, we'll create a `ShellCommand` component that executes a shell command.


### 1. Scaffold the new component file

First, scaffold the `ShellCommand` component. You can scaffold a component with either a YAML or Pythonic interface.

<Tabs groupId="interface">
    <TabItem value="yaml" label="YAML interface">

      To scaffold a component with a YAML interface, use the `dg scaffold component` command:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/generated/1-dg-scaffold-shell-command.txt" />

        The above command will add a new file to the `components` directory of your Dagster project that contains the basic structure for the new component.
        
        The `ShellCommand` class inherits from <PyObject section="components" module="dagster" object="Model" />, <PyObject section="components" module="dagster" object="Component" /> and <PyObject section="components" module="dagster" object="Resolvable" />. `Model` is used to implement a YAML interface for the component, and makes the class that inherits from it (in this case, `ShellCommand`) into a [Pydantic model](https://docs.pydantic.dev/latest/concepts/models/):

        <CodeExample
          path="docs_snippets/docs_snippets/guides/components/shell-script-component/generated/2-shell-command-empty.py"
          language="python"
          title="src/my_project/components/shell_command.py"
        />

    </TabItem>
    <TabItem value="pythonic" label="Pythonic interface">
        To scaffold a component with a Pythonic interface, use the `dg scaffold component` command with the `--no-model` flag:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/pythonic/1-dg-scaffold-shell-command-no-model.txt" />

        The above command will add a new file to the `components` directory of your Dagster project that contains the basic structure for the new component.
        
        Since this component only needs a Python interface, the `ShellCommand` class does not inherit from <PyObject section="components" module="dagster" object="Model" />, and an empty `__init__` method is included:

        <CodeExample
          path="docs_snippets/docs_snippets/guides/components/shell-script-component/pythonic/2-shell-command-empty-no-model-init.py"
          language="python"
          title="src/my_project/components/shell_command.py"
        />

        :::info

        You can also use [`@dataclasses.dataclass`](https://docs.python.org/3/library/dataclasses.html#dataclasses.dataclass) to implement the `__init__` method:

        <CodeExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/pythonic/2-shell-command-empty-no-model-dataclass.py" language="python" title="src/my_project/components/shell_command.py" />

        :::
    </TabItem>
</Tabs>


### 2. Define the component schema

The next step is to define the information the component will need when it is used. The `ShellCommand` component will need the following information:

- The path to the shell script to be run (`script_path`)
- The assets the shell script is expected to produce (`asset_specs`)

In this example, we annotate the `ShellCommand` class with `script_path` and `asset_specs`.

<Tabs groupId="interface">
  <TabItem value="yaml" label="YAML interface">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-config-schema-yaml.py"
      language="python"
      title="src/my_project/components/shell_command.py"
    />
  </TabItem>
  <TabItem value="pythonic" label="Pythonic interface">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-config-schema-pythonic.py"
      language="python"
      title="src/my_project/components/shell_command.py"
    />
  </TabItem>
</Tabs>

  <PyObject section="components" module="dagster" object="Resolvable" /> handles deriving a YAML schema for the class that inherits from it (in this case, `ShellCommand`) based on what the class is annotated with.

  :::info

  In the example above, we use the annotation `asset_specs: Sequence[dg.ResolvedAssetSpec]` because the `ShellCommand` component produces more than one `AssetSpec`.
  
  If the component only produced one asset, the annotation would be `asset_spec: ResolvedAssetSpec`, and the `Sequence` import would be unnecessary.

  :::

#### Using Dagster models for common schema annotations

To simplify common use cases, Dagster provides models for common annotations, such as <PyObject section="components" module="dagster" object="ResolvedAssetSpec" />, which handles exposing a schema for defining <PyObject section="assets" module="dagster" object="AssetSpec" pluralize /> from YAML and resolving them before instantiating the component.

The full list of models is:

* <PyObject section="components" module="dagster" object="ResolvedAssetKey" />
* <PyObject section="components" module="dagster" object="ResolvedAssetSpec" />
* <PyObject section="components" module="dagster" object="AssetAttributesModel" />
* <PyObject section="components" module="dagster" object="ResolvedAssetCheckSpec" />

For more information, see the [Components Core Models API documentation](/api/dagster/components#core-models).

### 3. (Optional) Add metadata to your component

You can optionally include metadata for your component by overriding the `get_spec` method. This allows you to set fields like `owners` and `tags` that will be visible in the generated documentation:

<Tabs groupId="interface">
  <TabItem value="yaml" label="YAML interface">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-config-schema-meta-yaml.py"
      language="python"
      title="src/my_project/components/shell_command.py"
    />
  </TabItem>
  <TabItem value="pythonic" label="Pythonic interface">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-config-schema-meta-pythonic.py"
      language="python"
      title="src/my_project/components/shell_command.py"
    />
  </TabItem>
</Tabs>

### 4. Update the `build_defs` method

Finally, you'll need to define how to turn the component parameters into a `Definitions` object.

To do so, you will need to update the `build_defs` method, which is responsible for returning a `Definitions` object containing all definitions related to the component.

In this example, the `build_defs` method creates a `@multi_asset` that executes the provided shell script. By convention, the code to execute this asset is placed inside of a function called `execute`, which will make it easier for future developers to create subclasses of this component:

:::note

The `@multi_asset` decorator is used to provide the flexibility of assigning multiple assets using `asset_spec` to a single shell script execution as our shell script may produce more than one object.

:::

<Tabs groupId="interface">
  <TabItem value="yaml" label="YAML interface">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-build-defs-yaml.py"
      language="python"
      title="src/my_project/components/shell_command.py"
    />
  </TabItem>
  <TabItem value="pythonic" label="Pythonic interface">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/components/shell-script-component/with-build-defs-pythonic.py"
      language="python"
      title="src/my_project/components/shell_command.py"
    />
  </TabItem>
</Tabs>

## Registering a new component in your environment

Following the steps above will automatically register your component in your environment. To see your new component in the list of available components, run `dg list components`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/generated/3-dg-list-components.txt" />

You can also view automatically generated documentation describing your new component by running `dg dev` to start the webserver and navigating to the `Docs` tab for your project's code location:

<CliInvocationExample contents="dg dev" />

![Docs tab in Dagster webserver](/images/guides/labs/components/docs-in-UI.png)

## Adding component definitions to your project

After you create and register your new component, you can use it to add component definitions to your Dagster project with the `dg scaffold defs` command:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/shell-script-component/generated/4-scaffold-instance-of-component.txt" />
