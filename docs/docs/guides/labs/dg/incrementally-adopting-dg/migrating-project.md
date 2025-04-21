---
title: 'Converting an existing project to use dg'
sidebar_position: 100
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

Suppose we have an existing Dagster project. Our project defines a Python
package with a a single Dagster asset. The asset is exposed in a top-level
`Definitions` object in `my_existing_project/definitions.py`. We'll consider
both a case where we have been using [uv](https://docs.astral.sh/uv/) with `pyproject.toml` and [`pip`](https://pip.pypa.io/en/stable/) with `setup.py`.

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/1-uv-tree.txt" />
    </TabItem>
    <TabItem value="pip" label="pip">
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/1-pip-tree.txt" />
    </TabItem>
</Tabs>

`dg` needs to be able to resolve a Python environment for your project. This
environment must include an installation of your project package. By default,
a project's environment will resolve to whatever virtual environment is
currently activated in the shell, or system Python if no virtual environment is
activated.

Before proceeding, we'll make sure we have an activated and up-to-date virtual
environment in the project root. Having the virtual environment located in the
project root is recommended (particularly when using `uv`) but not required.

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">
        If you don't have a virtual environment yet, run:
        <CliInvocationExample contents="uv sync" />
        Then activate it:
        <CliInvocationExample contents="source .venv/bin/activate" />
    </TabItem>
    <TabItem value="pip" label="pip">
        If you don't have a virtual environment yet, run:
        <CliInvocationExample contents="python -m venv .venv" />
        Now activate it:
        <CliInvocationExample contents="source .venv/bin/activate" />
        And install the project package as an editable install:
        <CliInvocationExample contents="pip install --editable ." />
    </TabItem>
</Tabs>


## Install dependencies

### Install the `dg` command line tool

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">
        First let's [install `dg` globally](/guides/labs/dg) as a `uv` tool:
        <CliInvocationExample contents="uv tool install dagster-dg" />
        This installs `dg` into a hidden, isolated Python environment separate from your project virtual environment. The `dg` executable is always available in the user's `$PATH`, regardless of any virtual environment activation in the shell. This is the recommended way to work with `dg` if you are using `uv`.
    </TabItem>
    <TabItem value="pip" label="pip">
        Let's install `dg` into your project virtual environment. This is the recommended way to work with `dg` if you are using `pip`.
        <CliInvocationExample contents="pip install dagster-dg" />
    </TabItem>
</Tabs>

## Update project structure

### Add `dg` configuration

The `dg` command recognizes Dagster projects through the presence of [TOML
configuration](/guides/labs/dg/configuring-dg). This may be either a `pyproject.toml` file with a `tool.dg` section or a `dg.toml` file. Let's add this configuration:

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">
        Since our project already has a `pyproject.toml` file, we can just add
        the requisite `tool.dg` section to the file:

        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/3-uv-config.toml" language="toml" title="pyproject.toml" />
    </TabItem>
    <TabItem value="pip" label="pip">
        Since our sample project has a `setup.py` and no `pyproject.toml`,
        we'll create a `dg.toml` file:
        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/3-pip-config.toml" language="toml" title="dg.toml" />
    </TabItem>
</Tabs>

There are three settings:

- `directory_type = "project"`: This is how `dg` identifies your package as a Dagster project. This is required.
- `project.root_module = "my_existing_project"`: This points to the root module of your project. This is also required.
- `project.code_location_target_module = "my_existing_project.definitions"`: This tells `dg` where to find the top-level `Definitions` object in your project. This actually defaults to `[root_module].definitions`, so it is not strictly necessary for us to set it here, but we are including this setting in order to be explicit--existing projects might have the top-level `Definitions` object defined in a different module, in which case this setting is required.

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
