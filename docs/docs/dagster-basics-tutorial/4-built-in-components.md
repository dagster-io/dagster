---
title: Built-in components
description: Using built-in components in your project
sidebar_position: 50
---

Defining Dagster objects yourself can be powerful, but you do not always need to write Dagster code directly. [Components](/guides/build/components) provide a way to streamline development by generating Dagster objects for you through an intuitive interface.

Components can be used in a variety of situations:

- **Built-in components** let you easily integrate with common workflows (such as Python scripts) or with popular tools like [dbt](https://www.getdbt.com/) or [Fivetran](https://www.fivetran.com/).
- **Custom components** let you define your own to address specific use cases.

In this step, we will use a built-in component to turn a Python script into an asset without writing any Dagster objects.

## 1. Scaffold the component

Dagster provides many built-in components as part of the `dagster-dg-cli` library. To view all the components in your Dagster project, run:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/commands/dg-list-components.txt" />

The component we will use is `dagster.PythonScriptComponent`, which can represent a Python script as an asset. To scaffold this component:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/commands/dg-scaffold-python-component.txt" />

This adds a new directory, `scripts`, within `defs`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/tree/step-3.txt" />

This directory contains the files needed to configure our component.

## 2. Configure the component

First, add a Python script to the `defs` directory of your Dagster project. This will be the script we turn into an asset:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/src/dagster_tutorial/defs/my_script.py"
  language="python"
  title="src/dagster_tutorial/defs/my_script.py"
/>

Next, configure the YAML for the component. The configuration interface for each component is unique. You can view the parameters for a component in the UI:

1. Navigate to **Deployment**.
2. Click the "dagster-tutorial" code location.
3. Click **Docs**.
4. Select the `dagster.PythonScriptComponent` component.

This view shows how to configure the component and the attributes available for customization.

For `dagster.PythonScriptComponent`, set `execution/path` to your Python script (relative to the root of the Dagster project). You can also connect it within the asset graph so it can be a dependency of another asset using `assets/deps`.

Now, set the configuration in the YAML file created when the component was scaffolded:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tutorials/dagster-tutorial/src/dagster_tutorial/defs/script/defs.yaml"
  language="yaml"
  title="src/dagster_tutorial/defs/script/defs.yaml"
/>

Run `dg check` again to ensure that everything is configured correctly.

## 3. Materialize the assets

In the Dagster UI at [http://127.0.0.1:3000](http://127.0.0.1:3000), you will see a new asset downstream of `customers` called `script`. Select and materialize this asset to have Dagster execute it.