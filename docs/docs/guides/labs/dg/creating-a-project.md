---
title: 'Creating a project with dg'
description: Dagster dg allows you to create a special type of Python package, called a project, that defines a Dagster code location.
sidebar_label: 'Creating a project'
sidebar_position: 100
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';
import InstallUv from '@site/docs/partials/\_InstallUv.md';

<DgComponentsPreview />

`dg` allows you to create a special type of Python package, called a _project_, that defines a [Dagster code location](/guides/deploy/code-locations/managing-code-locations-with-definitions).

:::note

Dagster projects created with `dg` are compatible with Dagster Components. For more information, see the [Dagster Components documentation](/guides/labs/components).

:::

## Prerequisites

Before creating a project with `dg`, you must [install `dg`](/guides/labs/dg#installation).

## Creating a project

<Tabs>
  <TabItem value="uv" label="uv">
    ``` dg scaffold project my-project ```
  </TabItem>
  <TabItem value="pip" label="pip">
    ``` dg scaffold project my-project ```
  </TabItem>
</Tabs>

## Project structure

The `dg scaffold project` command creates a directory with a standard Python package structure with some additions:

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

- The Python package `my-project` lives in `src/my-project` and contains the deployable code that defines
  your Dagster pipelines.
- `my-project/defs` will contain your Dagster definitions.
- `my-project/lib` is where you will define custom component types, and
  optionally other code you wish to share across Dagster definitions.
- `my-project/definitions.py` is the entry point that Dagster will load when
  deploying your code location. It is configured to load all definitions from
  `my-project/defs`. You should not need to modify this file.
- `tests` is a separate Python package defined at the top level (outside
  `src`). It should contain tests for the `my-project` package.
- `pyproject.toml` is a standard Python package configuration file. In addition
  to the regular Python package metadata, it contains a `tool.dg` section
  for `dg`-specific settings.
- `uv.lock` is the [lockfile](https://docs.astral.sh/uv/concepts/projects/layout/#the-lockfile) for the Python package manager [`uv`](https://docs.astral.sh/uv/). `dg` projects use `uv` by default. For more information, see [`uv` integration](/guides/labs/dg/python-environment-management-and-uv-integration).
