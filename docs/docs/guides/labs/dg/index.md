---
description: dg is a new command line interface that provides a streamlined Dagster development experience that can be used in existing Dagster projects or used to scaffold new projects. You can use dg to list, check, and scaffold Dagster definitions and components.
sidebar_position: 10
title: dg
---

import InstallUv from '@site/docs/partials/\_InstallUv.md';
import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

`dg` is a new command line interface that provides a streamlined Dagster development experience. It is a drop-in replacement for the Dagster CLI that can be [used in existing projects](/guides/labs/dg/incrementally-adopting-dg/migrating-project) or used to [scaffold new Dagster projects](/guides/labs/dg/creating-a-project). Once a project is set up to use `dg`, you can list, check, and scaffold Dagster definitions and [components](/guides/labs/components/) with ease.

:::note

`dg` is designed to be usable from an isolated environment and has no dependency on `dagster` itself.

:::

## Installation

You can install `dg` from a package manager or via `curl` with our standalone installer script.

<Tabs>
<TabItem value="brew" label="Homebrew">

`dg` is available in a Homebrew tap:

<CliInvocationExample contents="brew install dagster-io/tap/dg" />

</TabItem>
<TabItem value="curl" label="curl">

Use `curl` to download a standalone installation script and execute it with `sh`:

<CliInvocationExample contents="curl -LsSf https://dagster.io/dg/install.sh | sh" />

Request a specific version by including it in the URL:

<CliInvocationExample contents="curl -LsSf https://dagster.io/dg/1.10.14/install.sh | sh" />

</TabItem>
<TabItem value="uv" label="uv">

First, install the Python package manager [`uv`](https://docs.astral.sh/uv/) if you don't have it:

<InstallUv />

Next, use `uv` to install `dg` as a globally available tool:

<CliInvocationExample contents="uv tool install dagster-dg" />

This installs `dg` into a hidden, isolated Python environment. The `dg` executable is always available in your `$PATH`, regardless of any virtual environment activation in the shell.

While it is possible to create a virtual environment and install `dagster-dg` into it with `uv`, we recommend a global installation for most users, since it only needs to be done once, and better supports multiple Python projects.

</TabItem>
<TabItem value="pip" label="pip">

If you are starting a project from scratch, run the following:

```
mkdir my_project && cd my_project
```

```
python -m venv .venv && source .venv/bin/activate
```

If you are not starting a new project, first activate your desired virtual
environment, then install `dagster-dg`:

```
pip install dagster-dg
```

</TabItem>
</Tabs>

## `dg` CLI reference

Once you've installed `dg`, you can run `dg --help` on the command line to see all the commands, or check out the [`dg` CLI documentation](/guides/labs/dg/dagster-dg-cli).