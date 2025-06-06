---
description: dg is a new command line interface that provides a streamlined Dagster development experience that can be used in existing Dagster projects or used to scaffold new projects. You can use dg to list, check, and scaffold Dagster definitions and components.
sidebar_position: 10
title: dg
---

import InstallUv from '@site/docs/partials/\_InstallUv.md';
import DgComponentsPreview from '@site/docs/partials/\_DgComponentsPreview.md';

<DgComponentsPreview />

`dg` is a new command line interface that provides a streamlined Dagster development experience. It is a drop-in replacement for the Dagster CLI that can be [used in existing projects](/guides/labs/dg/incrementally-adopting-dg/migrating-project) or in [new Dagster projects](/guides/labs/dg/creating-a-project) created with the `create-dagster` CLI. Once a project is set up to use `dg`, you can list, check, and scaffold Dagster definitions and [components](/guides/labs/components/) with ease.


## Installing the create-dagster CLI

New projects can be created using the `create-dagster` CLI. You can install `create-dagster` from a package manager or via `curl` with our standalone installer script.

<Tabs>
<TabItem value="uv" label="uv">

First, install the Python package manager [`uv`](https://docs.astral.sh/uv/) if you don't have it:

<InstallUv />

We recommend running `create-dagster` using [uvx](https://docs.astral.sh/uv/guides/tools/):

<CliInvocationExample contents="uvx -U create-dagster project my-project" />

This runs `create-dagster` in a temporary, isolated Python environment.

While it is also possible to create a virtual environment and install `create-dagster` into it with `uv`, using `uvx` better supports multiple Python projects and doesn't require an explicit install step.

</TabItem>

<TabItem value="brew" label="Homebrew">

`create-dagster` is available in a Homebrew tap:

<CliInvocationExample contents="brew install dagster-io/tap/create-dagster" />

</TabItem>

<TabItem value="curl" label="curl">

Use `curl` to download a standalone installation script and execute it with `sh`:

<CliInvocationExample contents="curl -LsSf https://dg.dagster.io/create-dagster/install.sh | sh" />

Request a specific version by including it in the URL:

<CliInvocationExample contents="curl -LsSf https://dg.dagster.io/create-dagster/1.10.18/install.sh | sh" />

`create-dagster` is available starting at version 1.10.18.

</TabItem>

</Tabs>

Once you have `create-dagster` installed (or available to run via `uvx`), see the [creating a new project guide](/guides/labs/dg/creating-a-project) to use it to create `dg` projects.
