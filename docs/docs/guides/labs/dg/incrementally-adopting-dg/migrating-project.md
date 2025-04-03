---
title: 'Converting an existing project to use dg'
sidebar_position: 200
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

:::note

This guide is only relevant if you are starting from an _existing_ Dagster project. This setup is unnecessary if you [scaffolded a new project](/guides/labs/dg/scaffolding-a-project) with `dg scaffold project`.

:::

We have a basic existing Dagster project and have been using `pip` to manage
our Python environment. Our project defines a Python package with a `setup.py`
and a single Dagster asset. The asset is exposed in a top-level `Definitions`
object in `my_existing_project/definitions.py`.

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/1-tree.txt" />

## Install dependencies

### Install the `dg` command line tool

Let's start with a fresh Python virtual environment (you may already have one):

<CliInvocationExample contents="python -m venv .venv && source .venv/bin/activate" />

We'll need to install the `dg` command line tool. You can install it into the
virtual environment using `pip`:

<CliInvocationExample contents="pip install dagster-dg" />

:::note
For simplicity in this tutorial, we are installing the `dg` executable into the
same virtual environment as our project. However, we generally recommend
installing `dg` globally using the
[`uv`](https://docs.astral.sh/uv/getting-started/installation/) package manager
via `uv tool install dagster-dg`. This will install `dagster-dg` into an
isolated environment and make it a globally available executable. This makes it
easier to work with multiple projects using `dg`.
:::

## Update project structure

### Add `pyproject.toml`

The `dg` command recognizes Dagster projects through the presence of a
`pyproject.toml` file with a `tool.dg` section. If you are already using
`pyproject.toml` for your project, you can just add the requisite `tool.dg`
to the file. Since our sample project has a `setup.py` and no `pyproject.toml`,
we need to create a new `pyproject.toml` file. This can co-exist with
`setup.py`-- it is purely a source of config for `dg`. Here is the config we
need to put in `pyproject.toml`:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/3-pyproject.toml" language="toml" title="pyproject.toml" />

There are three settings:

- `tool.dg.directory_type = "project"`: This is how `dg` identifies your package as a Dagster project. This is required.
- `tool.dg.project.root_module = "my_existing_project"`: This points to the root module of your project. This is also required.
- `tool.dg.project.code_location_target_module = "my_existing_project.definitions"`: This tells `dg` where to find the top-level `Definitions` object in your project. This actually defaults to `[root_module].definitions`, so it is not strictly necessary for us to set it here, but we are including this setting in order to be explicit--existing projects might have the top-level `Definitions` object defined in a different module, in which case this setting is required.
Now that these settings are in place, you can interact with your project using `dg`. If we run `dg list defs` we can see the sole existing asset in our project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/4-list-defs.txt"  />

### Create a `defs` directory

Part of the `dg` experience is _autoloading_ definitions. This means
automatically picking up any definitions that exist in a particular module. We
are going to create a new submodule named `my_existing_project.defs` (`defs` is
the conventional name of the module for where definitions live in `dg`) from which we will autoload definitions.

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/5-mkdir-defs.txt" />

## Modify top-level definitions

Autoloading is provided by a function that returns a `Definitions` object. Because we already have some other definitions in our project, we'll combine those with the autoloaded ones from `my_existing_project.defs`.

To do so, you'll need to modify your `definitions.py` file, or whichever file contains your top-level `Definitions` object.

You'll autoload definitions using `load_defs`, then merge them with your existing definitions using `Definitions.merge`. You pass `load_defs` the `defs` module you just created:
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

Now let's add an asset to the new `defs` module. Create
`my_existing_project/defs/autoloaded_asset.py` with the following contents:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/8-autoloaded-asset.py" />

Finally, let's confirm the new asset is being autoloaded. Run `dg list defs`
again and you should see both the new `autoloaded_asset` and old `my_asset`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/9-list-defs.txt"  />

Now your project is fully compatible with `dg`!

## Next steps

- [Restructure existing definitions](/guides/labs/dg/incrementally-adopting-dg/migrating-definitions)
- [Add a new definition to your project](/guides/labs/dg/dagster-definitions)
