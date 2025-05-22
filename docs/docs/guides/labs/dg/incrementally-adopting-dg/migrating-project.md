---
description: Convert an existing Dagster project to use dg.
sidebar_position: 100
title: Converting an existing project to use dg
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
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/2-a-uv-venv.txt" />
    Then activate it:
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/2-b-uv-venv.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    If you don't have a virtual environment yet, run:
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/2-a-pip-venv.txt" />
    Now activate it:
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/2-b-pip-venv.txt" />
    And install the project package as an editable install:
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/2-c-pip-venv.txt" />
  </TabItem>
</Tabs>

## Install dependencies

### Install the `dg` command line tool

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    We'll [install `dg` globally](/guides/labs/dg) as a `uv` tool:
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/3-uv-install-dg.txt" />
    This installs `dg` into a hidden, isolated Python environment separate from your project virtual environment. The
    `dg` executable is always available in the user's `$PATH`, regardless of any virtual environment activation in the
    shell. This is the recommended way to work with `dg` if you are using `uv`.
  </TabItem>
  <TabItem value="pip" label="pip">
    Let's install `dg` into your project virtual environment. This is the recommended way to work with `dg` if you are
    using `pip`.
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/3-pip-install-dg.txt" />
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

        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/4-uv-config.toml" language="toml" title="pyproject.toml" />
    </TabItem>
    <TabItem value="pip" label="pip">
        Since our sample project has a `setup.py` and no `pyproject.toml`,
        we'll create a `dg.toml` file:
        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/4-pip-config.toml" language="toml" title="dg.toml" />
    </TabItem>

</Tabs>

There are three settings:

- `directory_type = "project"`: This is how `dg` identifies your package as a Dagster project. This is required.
- `project.root_module = "my_existing_project"`: This points to the root module of your project. This is also required.
- `project.code_location_target_module = "my_existing_project.definitions"`: This tells `dg` where to find the top-level `Definitions` object in your project. This actually defaults to `[root_module].definitions`, so it is not strictly necessary for us to set it here, but we are including this setting in order to be explicit--existing projects might have the top-level `Definitions` object defined in a different module, in which case this setting is required.

Now that these settings are in place, you can interact with your project using `dg`. If we run `dg list defs` we can see the sole existing asset in our project:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/5-list-defs.txt" />

### Add a `dagster_dg.plugin` entry point

We're not quite done adding configuration. `dg` uses the Python [entry
point](https://packaging.python.org/en/latest/specifications/entry-points/) API
to expose custom component types and other scaffoldable objects from user
projects. Our entry point declaration will specify a submodule as the location
where our project exposes plugin objects. By convention, this submodule is
named `<root_module>.lib`. In our case, it will be `my_existing_project.lib`.
Let's create this submodule now:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/6-create-lib.txt" />

:::tip
See the [plugin guide](/guides/labs/components/creating-new-component-types/creating-dg-plugin) for more on `dg` plugins.
:::

We'll need to add a `dagster_dg.plugin` entry point to our project and then
reinstall the project package into our virtual environment. The reinstallation
step is crucial. Python entry points are registered at package installation
time, so if you simply add a new entry point to an existing editable-installed
package, it won't be picked up.

Entry points can be declared in either `pyproject.toml` or `setup.py`:

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">
        Since our package metadata is in `pyproject.toml`, we'll add the entry
        point declaration there:

        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/7-uv-plugin-config.toml" language="toml" title="pyproject.toml" />

        Then we'll reinstall the package. Note that `uv sync` will _not_
        reinstall our package, so we'll use `uv pip install` instead:
        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/8-uv-reinstall-package.txt" />

    </TabItem>
    <TabItem value="pip" label="pip">
        Our package metadata is in `setup.py`. While it is possible to add
        entry point declarations to `setup.py` directly, we want to be able to
        read the entry point declaration from `dg`, and there is no reliable
        way to read `setup.py` (since it is arbitrary Python code). So we'll
        instead add the entry point to a new `setup.cfg`, which can be used
        alongside `setup.py`. Create `setup.cfg` with the following contents
        (if your package has existing entry points declared in `setup.py`, you'll
        want to move their definitions to `setup.cfg` as well):
        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/7-pip-plugin-config.txt" language="ini" title="setup.cfg" />
        Then we'll reinstall the package:
        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/8-pip-reinstall-package.txt" />
    </TabItem>

</Tabs>

To make sure our plugin is working, let's scaffold a new component type and
then make sure it's available to `dg` commands. First create the component
type:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/9-scaffold-component-type.txt" />

Then run `dg list plugins` to confirm that the new component type is available:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/10-list-plugins.txt" />

You should see the `my_project.lib.MyComponentType` listed in the output. This
means our plugin entry point is working.

### Create a `defs` directory

Part of the `dg` experience is _autoloading_ definitions. This means
automatically picking up any definitions that exist in a particular module. We
are going to create a new submodule named `my_existing_project.defs` (`defs` is
the conventional name of the module for where definitions live in `dg`) from which we will autoload definitions.

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/11-mkdir-defs.txt" />

## Modify top-level definitions

Autoloading is provided by a function that returns a `Definitions` object. Because we already have some other definitions in our project, we'll combine those with the autoloaded ones from `my_existing_project.defs`.

To do so, you'll need to modify your `definitions.py` file, or whichever file contains your top-level `Definitions` object.

You'll autoload definitions using `load_defs`, then merge them with your existing definitions using `Definitions.merge`. You pass `load_defs` the `defs` module you just created:

<Tabs>
  <TabItem value="before" label="Before">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/dg/migrating-project/12-initial-definitions.py"
      language="python"
    />
  </TabItem>
  <TabItem value="after" label="After">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/dg/migrating-project/13-updated-definitions.py"
      language="python"
    />
  </TabItem>
</Tabs>

Now let's add an asset to the new `defs` module. Create
`my_existing_project/defs/autoloaded_asset.py` with the following contents:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/14-autoloaded-asset.py" />

Finally, let's confirm the new asset is being autoloaded. Run `dg list defs`
again and you should see both the new `autoloaded_asset` and old `my_asset`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/15-list-defs.txt" />

Now your project is fully compatible with `dg`!

## Next steps

- [Restructure existing definitions](/guides/labs/dg/incrementally-adopting-dg/migrating-definitions)
- [Add a new definition to your project](/guides/labs/dg/dagster-definitions)
