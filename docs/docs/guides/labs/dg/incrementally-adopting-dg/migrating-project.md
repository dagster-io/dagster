---
title: 'Converting an existing project to use dg'
sidebar_position: 200
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

:::note

This guide is only relevant if you are starting from an _existing_ Dagster project. This setup is unnecessary if you [scaffolded a new project](/guides/labs/dg/scaffolding-a-project) with `dg scaffold project`.

:::

Let's begin with a Dagster project that has some assets:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/1-tree.txt" />

## Install dependencies

### Install the `dg` command line tool

We'll need to install the `dg` command line tool, which is used to scaffold components. We recommend installing `dg` globally using the [`uv`](https://docs.astral.sh/uv/getting-started/installation/) package manager; it can also be installed using `pip`.

<CliInvocationExample contents="uv tool install dagster-dg" />

### Install `dagster-components`

Next, we'll need to install the `dagster-components` package.

Though this is optional, we generally recommend using a separate virtual environment for each project, which can be accomplished using `uv`:

<Tabs>
    <TabItem value='before' label='Using uv virtual environment'>
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/3-uv-venv.txt" />

        Then, we can use `uv sync` to install the dependencies from our `pyproject.toml`, and then install the `dagster-components` package:
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/4-uv-freeze.txt" />
    </TabItem>
    <TabItem value='after' label='Using pip'>
        <CliInvocationExample contents="pip install dagster-components" />
    </TabItem>

</Tabs>

## Update project structure

### Update `pyproject.toml`

Add a `tool.dg` section to your `pyproject.toml` file. This will tell the `dg` command line tool that this project is a valid Dagster project.

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/migrating-project/2-pyproject.toml"
  language="toml"
  title="pyproject.toml"
/>

### Create a `defs` directory

Next, you'll want to create a directory to contain any new definitions you add to your project. By convention, this directory is named `defs`, and exists at the top level of your project's Python module.

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/5-mkdir-defs.txt" />

## Modify top-level definitions

`dagster-components` provides a utility to create a `Definitions` object from your defs directory. Because you're working with an existing project, you'll want to combine your existing definitions with the ones from your defs directory.

To do so, you'll need to modify your `definitions.py` file, or whichever file contains your top-level `Definitions` object.

You can manually construct a set of definitions using `load_defs`, then merge them with your existing definitions using `Definitions.merge`. You point `load_defs` at the module you just created.

<Tabs>
  <TabItem value="before" label="Before">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/dg/migrating-project/6-initial-definitions.py"
      language="python"
    />
  </TabItem>
  <TabItem value="after" label="After">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/dg/migrating-project/7-updated-definitions.py"
      language="python"
    />
  </TabItem>
</Tabs>

Now, your project is fully compatible with `dg`! `dg` can be used to scaffold new definitions directly into the existing project.

## Next steps

- [Restructure existing definitions](/guides/labs/dg/incrementally-adopting-dg/migrating-definitions)
- [Add a new definition to your project](/guides/labs/dg/dagster-definitions)
