---
description: Create a dg plugin by defining a Python package with dg-legible classes and functions.
sidebar_position: 300
title: Creating a dg plugin
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

A `dg` plugin is a Python package that defines and exposes `dg`-legible
classes and functions (which we call _plugin objects_). Plugin objects include custom
component types, scaffolding classes, and more. Plugin objects that are exposed
by an installed `dg` plugin can be inspected and interacted with by `dg`
commands.

Any Python package can be made into a `dg` plugin by declaring an [entry
point](https://packaging.python.org/en/latest/specifications/entry-points/)
under the `dagster_dg.plugin` group in its package metadata:

```toml
[project.entry-points]
"dagster_dg.plugin" = { my_package = "my_package"}
```

The entry point indicates a module within the package that contains references
to plugin objects. As you can see, an entry points is defined as a key-value pair
of strings. For `dagster_dg.plugin` entry points:

- The entry point value must be the name of a Python module containing plugin
  object references. By convention, this is usually the top-level module name of
  a package, though any submodule may be specified.
- The entry point key is arbitrary and does not affect component type
  detection, but by convention should be set to the same string as the value
  (i.e. the module name).

:::note
New projects scaffolded by `dg` include a `dagster_dg.plugin` entry point,
and therefore are `dg` plugins out of the box. This allows a project to define
project-scoped component types etc.
:::

## Converting an existing package into a `dg` plugin

Let's step through the process of converting an existing Python package into a `dg` plugin. We'll:

- Define a custom component type in the package
- Add a `dagster_dg.plugin` entry point to the package metadata
- Confirm that the custom component type is available to `dg` commands

Let's start with a basic package called `my_library`. `my_library` is intended
to be a shared library across multiple Dagster projects. Currently it contains
assorted plain Python utilities, but we want to add a custom component type
that is discoverable by `dg`.

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/creating-dg-plugin/1-tree.txt" />

Since the focus of this guide is on exposing rather than authoring plugin objects, we'll use a dummy `EmptyComponent` for our custom component type. Let's put this in a new submodule at `src/my_library/empty_component.py`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/creating-dg-plugin/2-empty-component.py"
  language="python"
  title="src/my_library/empty_component.py"
/>

Now we'll add the `dagster_dg.plugin` entry point to the package metadata.

Following convention, we add the following entry point to the package metadata:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/creating-dg-plugin/3-pyproject.toml"
  language="toml"
  title="pyproject.toml"
/>

This is enough to set up our `my_library` as a `dg` plugin, but it isn't exposing
`EmptyComponent` yet. That's because `EmptyComponent` is defined in
`my_library.empty_component`, but our entry point is set to
`my_library`. So we'll need to import `EmptyComponent` in the top-level
`my_library` module, i.e. in `my_library/__init__.py`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/dg/creating-dg-plugin/4-init.py"
  language="python"
  title="src/my_library/__init__.py"
/>

Now if we install `my_library` into a Python environment and run `dg list
plugins` against that environment, we'll see
`my_library.EmptyComponent`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/creating-dg-plugin/5-list-plugins.txt" />

That's all there is to it. Any other plugin objects that we'd like to add to
`my_library` can be exposed by importing them in the top-level `my_library`
module.

:::note
Python entry points are registered at package installation time. If you are
developing a library that has already been installed as an editable, and you
add a `dagster_dg.plugin` entry point to it, the entry point will not be
detected by `dg` until the package is reinstalled with `pip install -e
path/to/my_library`, `uv pip install path/to/my_library`, or an equivalent command.
:::
