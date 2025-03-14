---
title: 'Scaffolding a project'
sidebar_position: 200
---

import Preview from '../../../partials/\_Preview.md';

<Preview />

A Dagster [code
location](/guides/deploy/code-locations/managing-code-locations-with-definitions)
is a deployable collection of Dagster definitions. Code locations are defined
in a Python package. `dg` provides support for scaffolding a special type of
Python package, called a _project_, that defines a code location.

Scaffolding a project is very simple:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/dg/scaffolding-project/1-scaffolding-project.txt"  />

This will generate a new directory called `my-project`. This is a standard
python package structure with some extra details:

<CliInvocationExample path="docs_beta_snippets/docs_beta_snippets/guides/dg/scaffolding-project/2-tree.txt"  />

- The top-level package `my_project` contains the deployable code that defines
  your Dagster pipelines.
- `my_project/defs` is where your Dagster definitions will go.
- `my_project/lib` is where you will define custom component types, and
  optionally other code you wish to share across Dagster definitions.
- `my_project/definitions.py` is the entry point that Dagster will load when
  deploying your code location. It is set up to load all definitions from
`my_project/defs`. You should not need to modify this file.
- `my_project_tests` contains tests for the code in `my_project`.
- `pyproject.toml` is a standard Python package configuration file. In addition
  to the regular Python package metadata, it contains a `tool.dg` section
  for `dg`-specific settings.
- `uv.lock` is the [lockfile](https://docs.astral.sh/uv/concepts/projects/layout/#the-lockfile) for Python package manager [`uv`](https://docs.astral.sh/uv/). `dg` projects
  use `uv` by default.
