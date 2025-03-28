---
title: 'pyproject.toml settings'
sidebar_position: 500
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

`pyproject.toml` contains `tool.dagster` and `tool.dg` sections:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/4-pyproject.toml"
  language="TOML"
  title="jaffle-platform/pyproject.toml"
/>

### `tool.dagster` section

The `tool.dagster` section of `pyproject.toml` is not `dg`-specific. This section specifies that a set of definitions can be loaded from the `jaffle_platform.definitions` module.

### `tool.dg` section

The `tool.dg` section contains `is_project` and `is_component_lib` settings.

#### `is_project` setting

`is_project = true` specifies that this project is a `dg`-managed Dagster project. Projects created with components are regular Dagster projects with a particular structure.

To understand the structure, let's look at the content of `jaffle_platform/definitions.py`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/5-definitions.py"
  language="Python"
  title="jaffle-platform/jaffle_platform/definitions.py"
/>

This call to `load_defs` will:

- discover the set of components defined in the project
- compute a set of `Definitions` from each component
- merge the component-specific definitions into a single `Definitions` object

`is_project` is telling `dg` that the project is structured in this way and therefore contains component instances. In the current project, component instances will be placed in the default location at `jaffle_platform/components`.

#### `is_component_lib` setting

`is_component_lib = true` specifies that the project is a component library. This means that the project may contain component types that can be referenced when generating component instances.

In a typical project, most components are likely to be instances of types defined in external libraries (e.g. `dagster-components`), but you can also define custom component types scoped to your project. That is why `is_component_lib` is set to `true` by default. Any scaffolded component types in `jaffle_platform` will be placed in the default location at `jaffle_platform/lib`.

You can also see that this module is registered under the `dagster_dg.library` entry point in `pyproject.toml`. This is what makes the components discoverable to `dg`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/components/index/6-pyproject.toml"
  language="TOML"
  title="jaffle-platform/pyproject.toml"
/>
