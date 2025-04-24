---
title: 'Creating a components-ready Dagster project'
sidebar_position: 100
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

After [installing dependencies](/guides/labs/components#installation), you can create a components-ready project. In the example below, we create a project called `jaffle-platform`:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/2-a-uv-scaffold.txt" />

This command builds a project and initializes a new Python virtual environment inside of it. When using `dg`'s default environment management behavior, you won't need to worry about activating this virtual environment yourself.

:::note

To create and manage multiple components-ready projects, see "[Managing multiple projects with dg](/guides/labs/dg/multiple-projects)". Each project will have its own `uv`-managed Python environment.

:::

## Project structure

Running `dg scaffold project <project-name>` creates a fairly standard Python project structure:

<CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/3-uv-tree.txt" />

The following files and directories are included:

- A Python package `jaffle_platform` located in `src/jaffle_platform`-- the name is an underscored inflection of the project root directory (`jaffle-platform`).
- An (empty) `tests` package.
- A `uv.lock` file.
- A `pyproject.toml` file.

:::note

For more information about the sections and settings in pyproject.toml, see "[pyproject.toml settings](/guides/labs/dg/configuring-dg)".

:::
