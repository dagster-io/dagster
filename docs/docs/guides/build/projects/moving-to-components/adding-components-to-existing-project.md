---
description: Use Components within an existing Dagster project without fully migrating to the Components architecture.
sidebar_position: 570
title: Use Components within an existing project
---

:::note

This guide shows how to add Components to an existing Dagster project without fully migrating to the Components architecture. If you want to fully migrate your project to be Components-compatible, see [Converting an existing project](/guides/build/projects/moving-to-components/migrating-project).

:::

Sometimes you want to use Components in your existing Dagster project without fully migrating to the Components architecture. This is useful when you want to leverage the power of Components for specific functionality while keeping your existing project structure intact, or for testing out Components in a project before committing to adjusting the project structure.

## Example project structure

Let's walk through an example with an existing project that has the following structure:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/adding-components-to-existing-project/1-tree.txt" />

This project has existing assets and jobs organized in `analytics` and `elt` modules, with a top-level `definitions.py` file that loads everything together:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/adding-components-to-existing-project/2-definitions-before.py"
  language="python"
  title="my_existing_project/definitions.py"
/>

## Add component configuration

For this example, we'll use the `dagster-sling` component for data replication. Add it to your project's virtual environment:

<CliInvocationExample contents="uv add dagster-sling" />

The Sling component relies on a Sling `replication.yaml` file to define how to replicate data. Create a new `elt/sling` directory to store it:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/adding-components-to-existing-project/4-mkdir.txt" />

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/adding-components-to-existing-project/5-replication.yaml"
  language="yaml"
  title="my_existing_project/elt/sling/replication.yaml"
/>

## Update your definitions

Now, you can configure an instance of the `SlingReplicationCollectionComponent` in our `definitions.py` file, and pass it to the `build_defs_for_component` utility. This function creates a `Definitions` object from a component, which you can then merge with your existing definitions:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/adding-components-to-existing-project/6-definitions.py"
  language="python"
  title="my_existing_project/definitions.py"
/>

## Next steps

- [Convert your project to be fully Components-compatible](/guides/build/projects/moving-to-components/migrating-project)
