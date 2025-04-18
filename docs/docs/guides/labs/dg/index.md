---
title: 'dg'
sidebar_position: 10
---

import InstallUv from '@site/docs/partials/\_InstallUv.md';
import DgComponentsPreview from '@site/docs/partials/\_dgComponentsPreview.md';

<DgComponentsPreview />

`dg` is a new command line interface that provides a streamlined Dagster development experience. It is a drop-in replacement for the Dagster CLI that can be [used in existing projects](/guides/labs/dg/incrementally-adopting-dg/migrating-project) or used to [scaffold new Dagster projects](/guides/labs/dg/scaffolding-a-project). Once a project is set up to use `dg`, you can list, check, and scaffold Dagster definitions and [components](/guides/labs/components/) with ease. `dg` is designed to be usable from an isolated environment and has no dependency on `dagster` itself.

## Installation

There are two basic approaches to installing `dg`:

<Tabs>
<TabItem value="uv" label="uv">

First, install the Python package manager [`uv`](https://docs.astral.sh/uv/) if you don't have it:

<InstallUv />

Next, use `uv` to install `dg` as a globally available tool:

<CliInvocationExample contents="uv tool install dagster-dg" />

This installs `dg` into a hidden, isolated Python environment. The `dg` executable is always available in the user's `$PATH`, regardless of any virtual environment activation in the shell.

While it is possible to create a virtual environment and install `dagster-dg` into it with `uv`, we recommend a global installation for most users. It is simpler, only needs to be done once, and better supports multiple Python projects.

</TabItem>
<TabItem value="pip" label="pip">

If you are starting a project from scratch:

```
mkdir my_project && cd my_project
```

```
python -m venv .venv && source .venv/bin/activate
```

If you are not starting a new project, then just activate your desired virtual
environment. Then:

```
pip install dagster-dg
```

</TabItem>
</Tabs>

## `dg` API reference

import DgReference from '@site/docs/partials/\_DgReference.md';

<DgReference />
