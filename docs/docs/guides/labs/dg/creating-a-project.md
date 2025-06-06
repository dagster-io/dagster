---
title: 'Creating a components-ready Dagster project'
description: dg allows you to create a special type of Python package, called a project, that defines a Dagster code location.
sidebar_position: 100
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';
import InstallUv from '@site/docs/partials/\_InstallUv.md';

<DgComponentsPreview />

The `create-dagster` CLI allows you to create a special type of Python package, called a _project_, that defines a [Dagster code location](/deployment/code-locations/managing-code-locations-with-definitions).

## Prerequisites

Before creating a project, you must [install `create-dagster`](/guides/labs/dg#installing-the-create-dagster-cli). If you're using `uv`, you can run `create-dagster` using `uvx`, without needing to install it first.

## Creating a project

<Tabs>
  <TabItem value="uv" label="uv">
    ``` uvx -U create-dagster project my-project ```
  </TabItem>
  <TabItem value="non-uv" label="Homebrew, curl, or pip">
    ``` create-dagster project my-project ```
  </TabItem>
</Tabs>

## Project structure

The `create-dagster project` command creates a directory with a standard Python package structure with some additions:

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/3-uv-tree.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/3-pip-tree.txt" />
  </TabItem>
</Tabs>

:::tip

To use `tree`, install it with `brew install tree` (Mac), or follow the [installation instructions](https://oldmanprogrammer.net/source.php?dir=projects/tree/INSTALL).

:::

- The Python package `my_project` lives in `src/my_project` and contains the deployable code that defines
  your Dagster pipelines.
- `my_project/defs` will contain your Dagster definitions.
- `my_project/components` is where you will define custom component types, and
  optionally other code you wish to share across Dagster definitions.
- `my_project/definitions.py` is the entry point that Dagster will load when
  deploying your code location. It is configured to load all definitions from
  `my_project/defs`. You should not need to modify this file.
- `tests` is a separate Python package defined at the top level (outside
  `src`). It should contain tests for the `my_project` package.
- `pyproject.toml` is a standard Python package configuration file. In addition
  to the regular Python package metadata, it contains a `tool.dg` section
  for `dg`-specific settings.
- `uv.lock` is the [lockfile](https://docs.astral.sh/uv/concepts/projects/layout/#the-lockfile) for the Python package manager [`uv`](https://docs.astral.sh/uv/). `dg` projects use `uv` by default. For more information, see [`uv` integration](/guides/labs/dg/python-environment-management-and-uv-integration).

## Next steps

* [Add Dagster definitions to your project](/guides/labs/dg/dagster-definitions)
* [Add Dagster Component definitions to your project](/guides/labs/components/building-pipelines-with-components/adding-component-definitions)
* [Create custom Dagster Components](/guides/labs/components/creating-new-components/creating-and-registering-a-component)
