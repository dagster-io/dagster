---
description: Convert an existing Dagster project to be compatible with Components.
sidebar_position: 550
title: Converting an existing project
---

In this guide, we walk through converting an existing Dagster project that defines a Python package with a single Dagster asset, which is exposed in a top-level `Definitions` object in `my_existing_project/definitions.py`.

:::note

We'll cover both the case of [uv](https://docs.astral.sh/uv) with `pyproject.toml`, and [`pip`](https://pip.pypa.io/en/stable) with `setup.py`.

:::

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    If you used [`uv`](https://docs.astral.sh/uv) to set up your Dagster project, you will have a `pyproject.toml` project configuration file:
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/1-uv-tree.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    If you used [`pip`](https://pip.pypa.io/en/stable) to set up your Dagster project, you will have a `setup.py` project configuration file:
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/1-pip-tree.txt" />
  </TabItem>
</Tabs>

## Step 1: Create and activate a virtual environment

First, you will need to make sure you have an activated and up-to-date virtual environment. We recommend creating the virtual environment in the project root (particularly when using `uv`), although it is not required.

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
    Next, activate it:
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/2-b-pip-venv.txt" />
    Finally, install the project package as an editable install:
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/2-c-pip-venv.txt" />
  </TabItem>
</Tabs>

## Step 2: Install dependencies

Next, you will need to install the `dg` command line tool into your project virtual environment.

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/3-uv-install-dg.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/3-pip-install-dg.txt" />
  </TabItem>
</Tabs>

## Step 3: Update project structure

### Step 3.1: Add `dg` configuration

The `dg` command recognizes Dagster projects through the presence of [TOML
configuration](/api/clis/dg-cli/dg-cli-configuration). This may be either a `pyproject.toml` file with `tool.dg` and `tool.dg.project` sections, or a `dg.toml` file.

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">
        Since the example project already has a `pyproject.toml` file, you just need to add `tool.dg` and `tool.dg.project` sections:

        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/4-uv-config.toml" language="toml" title="pyproject.toml" />
    </TabItem>
    <TabItem value="pip" label="pip">
        Since the example project has a `setup.py` file and no `pyproject.toml` file, you will need to create a `dg.toml` file:
        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/4-pip-config.toml" language="toml" title="dg.toml" />
    </TabItem>

</Tabs>

#### Configuration reference

* `directory_type = "project"`: This is how `dg` identifies your package as a Dagster project. This setting is required.
* `root_module = "my_existing_project"`: This points to the root module of your project. This setting is required.
* `code_location_target_module = "my_existing_project.definitions"`: This tells `dg` where to find the top-level `Definitions` object in your project. Since this setting defaults to `NAME_OF_ROOT_MODULE.definitions`, it is not strictly necessary to set it for this example. However, if your project has the top-level `Definitions` object defined in a different module, this setting is required.

### Step 3.2: Check configuration

Now that the project configuration file has been updated, you can interact with your project using `dg`. To check the configuration and see the one asset in this project, run `dg list defs`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/5-list-defs.txt" />

### Step 3.3: Add an entry point to the project for custom component types

`dg` uses the Python [entry point](https://packaging.python.org/en/latest/specifications/entry-points) API
to expose custom component types and other scaffoldable objects from user projects. In the project configuration file, the entry point specifies the location of a Python submodule where the project exposes registry modules.

:::note

By convention, this submodule is named `<root_module>.lib`, but in the case of a Dagster project, it is `<root_module>.components`.

:::

#### Step 3.3.1: Create submodule directory

First, create the submodule directory and `__init__.py` file:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/6-create-lib.txt" />

{/* :::tip */}
{/* See the [Registry modules guide](todo) for more on registry modules */}
{/* ::: */}

#### Step 3.3.2: Add entry point to project configuration file

Next, add a `dagster_dg_cli.registry_modules` entry point to your project configuration file, then
reinstall the project package into your virtual environment.

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">
        Since the package metadata is in `pyproject.toml`, you will need to add the entry
        point declaration there:

        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/7-uv-plugin-config.toml" language="toml" title="pyproject.toml" />

    </TabItem>
    <TabItem value="pip" label="pip">
        With `pip`, the package metadata is in `setup.py`. While it is possible to add
        entry point declarations to `setup.py` directly, you will want to be able to
        read the entry point declaration from `dg`, and there is no reliable
        way to read `setup.py` (since it is arbitrary Python code). Instead you will need to add the entry point to a new `setup.cfg` file, which can be used alongside `setup.py`.
        
        Create `setup.cfg` with the following contents:
        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/7-pip-plugin-config.txt" language="ini" title="setup.cfg" />

        :::note

        If your package has existing entry points declared in `setup.py`, you will need to move their definitions to `setup.cfg` as well.

        :::
    </TabItem>

</Tabs>

#### Step 3.3.3: Reinstall the project package

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">
        Reinstall the package. Note that `uv sync` will _not_
        reinstall your package, so you will need to use `uv pip install` instead:
        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/8-uv-reinstall-package.txt" />
    </TabItem>
    <TabItem value="pip" label="pip">
        Reinstall the package:
        <CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/8-pip-reinstall-package.txt" />
    </TabItem>
</Tabs>

:::warning

The reinstallation step is crucial. Python entry points are registered at package installation
time, so if you simply add a new entry point to an existing editable-installed package, it won't be picked up.

:::

### Step 3.4: Check configuration

If you've done everything correctly, you should now be able to run `dg list registry-modules` and see the module `my_existing_project.components`, which you have registered as an entry point, listed in the output:

<CliInvocationExample
path="docs_snippets/docs_snippets/guides/dg/migrating-project/9-list-registry-modules.txt"
/>

You can now scaffold a new component in your project, and it will be available to `dg` commands. First create the component:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/10-scaffold-component-type.txt" />

Then run `dg list components` to confirm that the new component is available:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/11-list-components.txt" />

You should see the `my_project.lib.MyComponentType` listed in the output.

### Step 3.5: Create a `defs` submodule

Part of the `dg` experience is _autoloading_ definitions. This means automatically picking up any definitions that exist in a particular module. In this step, you will create a new submodule named `my_existing_project.defs` (`defs` is
the conventional name of the module for where definitions live in `dg`) from which you will autoload definitions:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/12-mkdir-defs.txt" />

## Step 4: Modify top-level definitions

### Step 4.1: Modify `definitions.py` file

Autoloading is provided by a function that returns a `Definitions` object. Because there are already some other definitions in the example project, you will need to combine those with the autoloaded ones from `my_existing_project.defs`.

To do so, you'll need to modify your `definitions.py` file, or whichever file contains your top-level `Definitions` object.

You will autoload definitions using `load_from_defs_folder`, then merge them with your existing definitions using `Definitions.merge`. You pass `load_from_defs_folder` the `defs` submodule you just created:

<Tabs>
  <TabItem value="before" label="Before">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/dg/migrating-project/13-initial-definitions.py"
      language="python"
    />
  </TabItem>
  <TabItem value="after" label="After">
    <CodeExample
      path="docs_snippets/docs_snippets/guides/dg/migrating-project/14-updated-definitions.py"
      language="python"
    />
  </TabItem>
</Tabs>

### Step 4.2: Add an asset to new `defs` submodule

Next, add an asset to the new `defs` submodule. Create a file called `my_existing_project/defs/autoloaded_asset.py` with the following contents:

<CodeExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/15-autoloaded-asset.py" />

### Step 4.3: Confirm the new asset is autoloaded

Finally, confirm the new asset is being autoloaded. If you run `dg list defs` again, you should see both the new `autoloaded_asset` and old `my_asset`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/migrating-project/16-list-defs.txt" />

Now the project is fully compatible with `dg`!

## Next steps

- [Restructure existing definitions](/guides/build/projects/moving-to-components/migrating-definitions)
- [Add a new definition to your project](/api/clis/dg-cli/dg-cli-reference)
