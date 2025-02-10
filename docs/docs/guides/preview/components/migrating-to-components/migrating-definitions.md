---
title: 'Migrating existing Definitions to components'
sidebar_position: 350
---

:::note
This guide covers migrating existing Python `Definitions` to components. This guide presupposes a components-enabled project. See the [getting started guide](./) or [Making an existing code location components-compatible](./existing-code-location) guide for more information.
:::

When adding components to an existing Dagster code location, it is often useful to restructure your definitions into component folders, making it easier to eventually migrate them entirely to using components.

## Example project

Let's walk through an example of how to migrate existing definitions to components, with a project that has the following structure:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/1-tree.txt"  />

The root `Definitions` object combines definitions from various nested modules:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/2-definitions-before.py" title="my_existing_project/definitions.py" />

Each of these modules consolidates its own `Definitions` object:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/3-inner-definitions-before.py" title="my_existing_project/elt/definitions.py" />

We'll migrate the `elt` module to a component.

## Create a Definitions component

We'll start by creating a `Definitions` component for the `elt` module:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/4-scaffold.txt" />


This creates a new folder in `my_existing_project/components/elt-definitions`, with a `component.yaml` file. This component is rather simple, it just points to a file which contains a `Definitions` object.

Let's move the `elt` module's `definitions.py` file to the new component folder:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/6-mv.txt" />

Now, we can update the `component.yaml` file to point to the new `definitions.py` file:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/5-component-yaml.txt" title="my_existing_project/components/elt-definitions/component.yaml" />

Finally, we can update the root `definitions.py` file to no longer explicitly load the `elt` module's `Definitions`:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/7-definitions-after.py" title="my_existing_project/definitions.py" />

Now, our project structure looks like this:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/8-tree-after.txt" />

We can repeat the same process for our other modules.

## Next steps

- [Add a new component to your code location](./using-a-component)
- [Create a new component type](./creating-a-component)
