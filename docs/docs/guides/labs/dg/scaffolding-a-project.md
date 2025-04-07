---
title: 'Initializing a dg project'
sidebar_position: 100
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

`dg` provides support for generating a special type of Python package, called a _project_, that defines a [Dagster code location](https://docs.dagster.io/guides/deploy/code-locations/managing-code-locations-with-definitions).

To initialize a new project, use the `dg init` command:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/scaffolding-project/1-scaffolding-project.txt" />

## Project structure

The `dg init` command creates a directory with a standard Python package structure with some additions:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/scaffolding-project/2-tree.txt" />

- The top-level package `my_project` contains the deployable code that defines
  your Dagster pipelines.
- `my_project/defs` will contain your Dagster definitions.
- `my_project/lib` is where you will define custom component types, and
  optionally other code you wish to share across Dagster definitions.
- `my_project/definitions.py` is the entry point that Dagster will load when
  deploying your code location. It is configured to load all definitions from
  `my_project/defs`. You should not need to modify this file.
- `my_project_tests` contains tests for the code in `my_project`.
- `pyproject.toml` is a standard Python package configuration file. In addition
  to the regular Python package metadata, it contains a `tool.dg` section
  for `dg`-specific settings.
- `uv.lock` is the [lockfile](https://docs.astral.sh/uv/concepts/projects/layout/#the-lockfile) for the Python package manager [`uv`](https://docs.astral.sh/uv/). `dg` projects use `uv` by default. For more information, see [`uv` integration](/guides/labs/dg/uv-integration).
