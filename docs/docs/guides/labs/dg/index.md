---
title: 'dg'
sidebar_position: 10
---

import InstallUv from '@site/docs/partials/\_InstallUv.md';
import Preview from '@site/docs/partials/\_Preview.md';

<Preview />

`dg` is a new command line interface that provides a streamlined Dagster development experience. It is a drop-in replacement for the Dagster CLI that can be [used in existing projects](/guides/labs/dg/incrementally-adopting-dg/migrating-project) or used to [scaffold new Dagster projects](/guides/labs/dg/scaffolding-a-project). Once a project is set up to use `dg`, you can list, check, and scaffold Dagster definitions and [components](/guides/labs/components/) with ease. `dg` is designed to be usable from an isolated environment and has no dependency on `dagster` itself.

## Installation

There are two basic approaches to installing `dg`:

- A _project-scoped_ `dg` installation installs `dg` into an existing Python environment you would like to use when developing your project. Typically this will be a [virtual environment](https://docs.python.org/3/tutorial/venv.html). The `dg` executable will be available when the virtual environment is active. This is the traditional workflow for Python developer tools. A project-scoped installation can be done with any Python package manager.
- A _global_ `dg` installation installs `dg` into a hidden, isolated Python environment. The `dg` executable is always available in the user's `$PATH`, regardless of any virtual environment activation in the shell. A global installation is simpler, only needs to be done once, and better supports multiple Python projects. We recommend a global installation for most users. A global installation requires the Python package manager [`uv`](https://docs.astral.sh/uv/).

<Tabs>
<TabItem value="global-uv" label="Global installation with `uv` (recommended)">

First, install the Python package manager `uv` if you don't have it:

<InstallUv />

Next, use `uv` to install `dg` as a globally available tool:

<CliInvocationExample contents="uv tool install dagster-dg" />

:::note
If you have a local clone of the `dagster` repo, you can install the `dg` executable as an editable by running `make install_editable_uv_tools` in the root folder of the repo. This will execute `uv tool install -e /path/to/dagster-dg`.
:::
</TabItem>
<TabItem value="project-scoped-uv" label="Project-scoped installation with `uv`">

First, install the Python package manager `uv` if you don't have it:

<InstallUv />

If you are using `uv`'s [project
environment](https://docs.astral.sh/uv/concepts/projects/layout/#the-project-environment) management, run:

```
uv add dagster-dg
```

If you are instead managing your own virtual environment, activate it and run:

```
uv pip install dagster-dg
```

</TabItem>
<TabItem value="project-scoped-pip" label="Project-scoped installation with `pip`">
Activate your virtual environment (if using one), then run:

```
uv pip install dagster-dg
```
</TabItem>
</Tabs>

## `dg` API reference

import DgReference from '@site/docs/partials/\_DgReference.md';

<DgReference />
