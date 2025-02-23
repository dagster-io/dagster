---
title: 'Using existing definitions with components'
sidebar_position: 100
---

:::note
This guide covers using existing Python definitions with components. This guide presupposes a components-enabled project. See the [getting started guide](/guides/labs/components/) or [Making an existing project components-compatible](/guides/labs/components/incrementally-adopting-components/existing-project) guide for more information.
:::

When adding components to an existing Dagster project, it is often useful to restructure your definitions into component folders, making it easier to eventually migrate them entirely to using components.

## Example project

Let's walk through an example of how to use existing definitions with components, with a project that has the following structure:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/1-tree.txt"  />

At the top level, we load definitions from various modules:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/2-definitions-before.py" title="my_existing_project/definitions.py" />

Each of these modules contains a variety of Dagster definitions, including assets, jobs, and schedules.

Let's migrate the `elt` module to a component.

## Create a Definitions component

We'll start by creating a `Definitions` component for the `elt` module:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/3-scaffold.txt" />

This creates a new folder in `my_existing_project/components/elt-definitions`, with a `component.yaml` file. This component requires a `definitions_path` parameter, which points to a file that contains a `Definitions` object.

Let's begin by moving the `elt` module's contents to the new component folder:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/4-mv.txt" />

Next, let's create a new `definitions.py` file in the component folder, which will collect all of the `elt` module's definitions into a single `Definitions` object:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/5-elt-nested-definitions.py" title="my_existing_project/components/elt-definitions/definitions.py" />

Finally, we can update the `component.yaml` file to point to the new `definitions.py` file:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/6-component-yaml.txt" title="my_existing_project/components/elt-definitions/component.yaml" />

Now that our component is defined, we can update the root `definitions.py` file to no longer explicitly load the `elt` module's `Definitions`:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/7-definitions-after.py" title="my_existing_project/definitions.py" />

Now, our project structure looks like this:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/8-tree-after.txt" />

We can repeat the same process for our other modules.

## Fully migrated project

Once each of our definitions modules are migrated to components, our project is left with a standardized structure.

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/9-tree-after-all.txt" />

Our project root now only constructs Definitions from components:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/migrating-definitions/10-definitions-after-all.py" title="my_existing_project/definitions.py" />

## Next steps

- [Add a new component to your project](/guides/labs/components/building-pipelines-with-components/adding-components)
- [Create a new component type](/guides/labs/components/creating-new-component-types/creating-and-registering-a-component-type)
