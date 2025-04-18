---
title: 'Initializing a dg project'
sidebar_position: 100
---

import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';
import InstallUv from '@site/docs/partials/\_InstallUv.md';

<DgComponentsPreview />

`dg` provides support for generating a special type of Python package, called a _project_, that defines a [Dagster code location](https://docs.dagster.io/guides/deploy/code-locations/managing-code-locations-with-definitions). `dg` can be used with any Python package manager, but we recommend [uv](https://docs.astral.sh/uv/) for the best experience.

<Tabs groupId="package-manager">
    <TabItem value="uv" label="uv">
        :::note Install uv
        <InstallUv />
        :::

        Ensure you have `dg` [installed globally](/guides/labs/dg) as a `uv` tool:

        <CliInvocationExample contents="uv tool install dagster-dg" />

        Now run the below command. Say yes to the prompt to run `uv sync` after scaffolding:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/scaffolding-project/2-a-uv-scaffold.txt" />

        The `dg init` command builds a project at `my-project`. Running `uv sync` after scaffolding creates a virtual environment and installs the dependencies listed in `pyproject.toml`, along with `my-project` itself as an [editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html). Now let's enter the directory and activate the virtual environment:

        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/scaffolding-project/2-b-uv-scaffold.txt" />
    </TabItem>
    <TabItem value="pip" label="pip">
        Because `pip` does not support global installations, you will install `dg` inside your project virtual environment.
        We'll create and enter our project directory, initialize and activate a virtual environment, and install the `dagster-dg` package into it:
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/scaffolding-project/2-a-pip-scaffold.txt" />
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/scaffolding-project/2-b-pip-scaffold.txt" />
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/scaffolding-project/2-c-pip-scaffold.txt" />
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/scaffolding-project/2-d-pip-scaffold.txt" />
        The `dg` executable is now available via the activated virtual environment. Let's run `dg init .` to scaffold a new project. The `.` tells `dg` to scaffold the project in the current directory.
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/scaffolding-project/2-e-pip-scaffold.txt" />
        Finally, install the newly created project package into the virtual environment as an [editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html):
        <CliInvocationExample path="docs_snippets/docs_snippets/guides/dg/scaffolding-project/2-f-pip-scaffold.txt" />
    </TabItem>

</Tabs>

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
