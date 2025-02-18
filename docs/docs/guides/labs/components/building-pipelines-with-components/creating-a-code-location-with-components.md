---
title: 'Creating a code location with Components'
sidebar_position: 100
---

:::note Prerequisites

Before creating a project with Components, you must follow the [steps to install `uv` and `dg`](/guides/labs/components/index.md#installation).

:::

After installing dependencies, you can scaffold a Components-ready code location for your project:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/2-scaffold.txt"  />

This command builds a code location and initializes a new Python
virtual environment inside of it. When using `dg`'s default environment
management behavior, you won't need to worry about activating this virtual environment yourself.

## Overview of files and directories

Let's have a look at the scaffolded files:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/3-tree.txt" />

You can see that we have a fairly standard Python project structure. The following files and directories are included:

- A Python package `jaffle_platform`-- the name is an underscored inflection of the
project root directory (`jaffle_platform`).
- An (empty) `jaffle_platform_tests` test package
- A `uv.lock` file
- A `pyproject.toml` file

### pyproject.toml

The `pyproject.toml` contains a `tool.dagster` and `tool.dg` section that look like
this:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/4-pyproject.toml" language="TOML" title="jaffle-platform/pyproject.toml" />

#### tool.dagster section

The `tool.dagster` section of `pyproject.toml` is not `dg`-specific. This section specifies that a set of definitions can be loaded from the `jaffle_platform.definitions` module.

#### tool.dg section

The `tool.dg` section contains two settings requiring more explanation: `is_code_location` and `is_component_lib`.

##### is_code_location setting

`is_code_location = true` specifies that this project is a `dg`-managed Dagster code location. Code locations created with Components are regular Dagster code locations with a particular structure.

To understand the structure, let's look at the content of `jaffle_platform/definitions.py`:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/5-definitions.py" language="Python" title="jaffle-platform/jaffle_platform/definitions.py" />

This call to `build_component_defs` will:

- discover the set of Components defined in the project
- compute a set of `Definitions` from each Component
- merge the Component-specific definitions into a single `Definitions` object

`is_code_location` is telling `dg` that the project is structured in this way and therefore contains Component instances. In the current project, Component instances will be placed in the default location at `jaffle_platform/components`.

##### is_component_lib setting

`is_component_lib = true` specifies that the project is a Component library. This means that the project may contain Component types that can be referenced when generating Component instances. In a typical code location, most Components
are likely to be instances of types defined in external libraries (e.g. `dagster-components`), but you can also define custom Component types scoped to your project. That is why `is_component_lib` is set to `true` by default. Any scaffolded component types in `jaffle_platform` will be placed in the default location at `jaffle_platform/lib`. You can also see that this
module is registered under the `dagster.components` entry point in `pyproject.toml`. This is what makes the components discoverable to `dg`:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/6-pyproject.toml" language="TOML" title="jaffle-platform/pyproject.toml" />

## Next steps

After scaffolding your code location with Components, you can [add more Components](adding-components) to complete your pipeline.