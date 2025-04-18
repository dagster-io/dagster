---
title: 'Initializing a dg project'
sidebar_position: 100
---

import DgComponentsPreview from '@site/docs/partials/\_dgComponentsPreview.md';
import InitializeDgProject from '@site/docs/partials/\_InitializeDgProject.md';

<DgComponentsPreview />

`dg` provides support for generating a special type of Python package, called a _project_, that defines a [Dagster code location](https://docs.dagster.io/guides/deploy/code-locations/managing-code-locations-with-definitions). `dg` can be used with any Python package manager, but we recommend [uv](https://docs.astral.sh/uv/) for the best experience.

<InitializeDgProject />

## Project structure

The `dg init` command creates a directory with a standard Python package structure with some additions:

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/3-uv-tree.txt" />
    </TabItem>
    <TabItem value="pip" label="pip">
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/3-pip-tree.txt" />
    </TabItem>
</Tabs>

- The Python package `my_project` lives in `src/my_project` and contains the deployable code that defines
  your Dagster pipelines.
- `my_project/defs` will contain your Dagster definitions.
- `my_project/lib` is where you will define custom component types, and
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
