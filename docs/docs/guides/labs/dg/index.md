---
title: 'dg'
sidebar_position: 10
---

import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

`dg` is a new command line interface that provides a streamlined Dagster development experience. It is a drop-in replacement for the Dagster CLI that can be [used in existing projects](/guides/labs/dg/incrementally-adopting-dg/migrating-project) or used to [scaffold new Dagster projects](/guides/labs/dg/scaffolding-a-project). Once a project is set up to use `dg`, you can list, check, and scaffold Dagster definitions and [components](/guides/labs/components/) with ease. `dg` is designed to be usable from an isolated environment and has no dependency on `dagster` itself.

## Installation

There are two basic approaches to installing `dg`:

- A _local_ `dg` installation installs `dg` into a particular user-managed virtual
  environment. The `dg` executable will be available when the
  virtual environment is active. This is the traditional workflow for Python
  developer tools. A local installation can be done with any Python package manager.
- A _global_ `dg` installation installs `dg` into a hidden, isolated Python
  environment. The `dg` executable is always available in the user's `$PATH`,
  regardless of any virtual environment activation in the shell. A global
  installation is simpler, only needs to be done once, and better supports
  multiple Python projects. We recommend a global installation for most users.
  A global installation requires the Python package manager [`uv`](https://docs.astral.sh/uv/).

<Tabs>
<TabItem value="local" label="local installation">
    Activate your virtual environment (if using one) and run:

    ```
    pip install dagster-dg`
    ```
</TabItem>
<TabItem value="global" label="global installation">

First, install the Python package manager `uv`:

<CliInvocationExample contents="brew install uv" />

For more information on `uv`, including installation instructions for non-Mac systems, see the [`uv` docs](https://docs.astral.sh/uv/).

Next, use `uv` to install `dg` as a global "tool":

<CliInvocationExample contents="uv tool install dagster-dg" />

:::tip

`uv tool install` installs Python packages from PyPI into isolated environments and exposes their executables on your shell path. This means the `dg` command will always execute in an isolated environment separate from any project environment.

:::


:::note
If you have a local clone of the `dagster` repo, you can install a as an editable by running `make install_editable_uv_tools` in the root folder of the repo. This will create an isolated environment for `dg` like the standard `uv tool install`, but the environment will contain an editable installation of `dagster-dg`.
:::
</TabItem>
</Tabs>

## `dg` API reference

import DgReference from '@site/docs/partials/\_DgReference.md';

<DgReference />
