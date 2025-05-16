---
description: Moving existing Dagster definitions to the defs directory of a dg-compatible project.
sidebar_position: 100
title: Autoloading existing Dagster definitions
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

:::note

This guide covers using existing Dagster definitions with a `dg`-compatible project. To convert an existing project to use `dg`, see "[Converting an existing project to use `dg`](/guides/labs/dg/incrementally-adopting-dg/migrating-project)".

:::

In projects that are started with `dg`, all definitions are typically kept in the `defs/` directory. However, if you've converted an existing project to use `dg`, you may have definitions located in various other modules. This guide will show you how to move these existing definitions into the `defs` directory in a way that will allow them to be automatically loaded.

## Example project structure

Let's walk through an example of migrating your existing definitions, with a project that has the following structure:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-definitions/1-tree.txt" />

At the top level, we load definitions from various modules:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/migrating-definitions/2-definitions-before.py"
  startAfter="start"
  title="my_existing_project/definitions.py"
/>

Each of these modules contains a variety of Dagster definitions, including assets, jobs, and schedules.

Let's migrate the `elt` module to a component.

## Move definitions to `defs`

We'll start by moving the top-level `elt` module into `defs/elt`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-definitions/3-mv.txt" />

Now that our definitions are in the `defs` directory, we can update the root `definitions.py` file to no longer explicitly load the `elt` module's `Definitions`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/migrating-definitions/4-definitions-after.py"
  title="my_existing_project/definitions.py"
/>

Our project structure now looks like this:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-definitions/5-tree-after.txt" />

The `load_defs` command in our `definitions.py` file will automatically load any definitions found within the `defs` module. This means that all of our definitions are now automatically loaded, with no need to import them up into any top-level organization scheme.

We can repeat the same process for our other modules.

## Fully migrated project structure

Once each of our definitions modules are migrated, our project is left with a standardized structure:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-definitions/6-tree-after-all.txt" />

Our project root now only constructs definitions from the `defs` module:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/migrating-definitions/7-definitions-after-all.py"
  title="my_existing_project/definitions.py"
/>

We can run `dg list defs` to confirm that all of our definitions are being loaded correctly:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/migrating-definitions/8-list-defs-after-all.txt"
  title="my_existing_project/definitions.py"
/>

## Next steps

- [Add a new definition to your project](/guides/labs/dg/dagster-definitions)
