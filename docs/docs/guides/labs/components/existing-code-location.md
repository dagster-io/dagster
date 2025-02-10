---
title: 'Making an existing code location components-compatible'
sidebar_position: 300
---

:::info

This feature is still in development and might change in patch releases. It’s not production-ready, and the documentation may also evolve. Stay tuned for updates.

:::

:::note

This guide is only relevant if you are starting from an _existing_ Dagster code location. This setup is unnecessary if you used `dg code-location generate` to create your code location.

:::

Let's begin with a Dagster code location that has some assets, but no components:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/existing-project/1-tree.txt"  />

## Install dependencies

### Install the `dg` command line tool

We'll need to install the `dg` command line tool, which is used to scaffold components. We recommend installing `dg` globally using the [`uv`](https://docs.astral.sh/uv/getting-started/installation/) package manager; it can also be installed using `pip`.

<CliInvocationExample contents="uv tool install dagster-dg" />

### Install `dagster-components`

Next, we'll need to install the `dagster-components` package.

Though this is optional, we generally recommend using a separate virtual environment for each code location, which can be accomplished using `uv`:

<Tabs>
    <TabItem value='before' label='Using uv virtual environment'>
        <CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/existing-project/3-uv-venv.txt" />

        Then, we can use `uv sync` to install the dependencies from our `pyproject.toml`, and then install the `dagster-components` package:
        <CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/existing-project/4-uv-freeze.txt" />
    </TabItem>
    <TabItem value='after' label='Using pip'>
        <CliInvocationExample contents="pip install dagster-components" />
    </TabItem>
</Tabs>

## Update project structure

### Update `pyproject.toml`

Add a `tool.dg` section to your `pyproject.toml` file. This will tell the `dg` command line tool that this code location is a valid Dagster code location.

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/existing-project/2-pyproject.toml" language="toml" title="pyproject.toml" />


### Create a `components` directory

Next, you'll want to create a directory to contain any new components you add to your code location. By convention, this directory is named `components`, and exists at the top level of your code location's Python module.

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/existing-project/5-mkdir-components.txt" />

## Modify top-level definitions

`dagster-components` provides a utility to create a `Definitions` object from your components directory. Because you're working with an existing code location, you'll want to combine your existing definitions with the ones from your components directory.

To do so, you'll need to modify your `definitions.py` file, or whichever file contains your top-level `Definitions` object.

You can manually construct a set of definitions for your components using `build_component_defs`, then merge them with your existing definitions using `Definitions.merge`. You point `build_components_defs` at the directory you just created that contains components.

<Tabs>
    <TabItem value='before' label='Before'>
        <CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/existing-project/6-initial-definitions.py" language="python" />
    </TabItem>
    <TabItem value='after' label='After'>
        <CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/existing-project/7-updated-definitions.py" language="python" />
    </TabItem>
</Tabs>

Now, your code location is ready to use components! `dg` can be used to scaffold new components directly into the existing code location.

## Next steps

- [Migrate existing definitions to components](./migrating-definitions)
- [Add a new component to your code location](./using-a-component)
- [Create a new component type](./creating-a-component)
