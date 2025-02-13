---
title: 'Creating a code location with Components'
sidebar_position: 100
---

:::note Prerequisites

Before creating a project with Components, you must follow the [steps to install `uv` and `dg`](/guides/labs/components/index.md#installation).

:::

After installing dependencies, you can scaffold a Components-ready code location for the project:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/2-scaffold.txt"  />

This command builds a code location at `jaffle-platform` and initializes a new Python
virtual environment inside of it. When using `dg`'s default environment
management behavior, you won't need to worry about activating this virtual environment yourself.

Let's have a look at the scaffolded files:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/3-tree.txt" />


You can see that we have a fairly standard Python project structure. There is a
python package `jaffle_platform`-- the name is an underscored inflection of the
project root directory (`jaffle_platform`). There is also an (empty)
`jaffle_platform_tests` test package, a `pyproject.toml`, and a `uv.lock`. The
`pyproject.toml` contains a `tool.dagster` and `tool.dg` section that look like
this:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/4-pyproject.toml" language="TOML" title="jaffle-platform/pyproject.toml" />


The `tool.dagster` section is not `dg`-specific, it specifies that a set of definitions can be loaded from the `jaffle_platform.definitions` module. The `tool.dg` section contains two settings requiring more explanation.

`is_code_location = true` specifies that this project is a `dg`-managed code location. This is just a regular Dagster code location that has been structured in a particular way. Let's look at the content of `jaffle_platform/definitions.py`:


<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/5-definitions.py" language="Python" title="jaffle-platform/jaffle_platform/definitions.py" />
This call to `build_component_defs` will:

- discover the set of components defined in the project
- compute a set of `Definitions` from each component
- merge the component-specific definitions into a single `Definitions` object

`is_code_location` is telling `dg` that the project is structured in this way and therefore contains component instances. In the current project, component instances will be placed in the default location at `jaffle_platform/components`.

`is_component_lib = true` specifies that the project is a component library.
This means that the project may contain component types that can be referenced
when generating component instances. In a typical code location most components
are likely to be instances of types defined in external libraries (e.g.
`dagster-components`), but it can also be useful to define custom component
types scoped to the project. That is why `is_component_lib` is set to `true` by
default. Any scaffolded component types in `jaffle_platform` will be placed in
the default location at `jaffle_platform/lib`. You can also see that this
module is registered under the `dagster.components` entry point in
`pyproject.toml`. This is what makes the components discoverable to `dg`:

<CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/components/index/6-pyproject.toml" language="TOML" title="jaffle-platform/pyproject.toml" />


Now that we've got a basic scaffold, we're ready to start building components. We are going to set up a data platform using Sling to ingest data and DBT to process the data. We'll then automate the daily execution of our pipeline using Dagster automation conditions.
