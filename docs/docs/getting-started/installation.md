---
title: Installing Dagster
description: Learn how to install Dagster and create projects with the dg CLI.
sidebar_position: 20
sidebar_label: Installation
---

import InstallUv from '@site/docs/partials/\_InstallUv.md';

:::note

To follow the steps in this guide, you'll need to install [Python 3.9](https://www.python.org/downloads/) or higher. **Python 3.13 is recommended**.

:::

To get started with Dagster, you can scaffold a new project with the [`create-dagster` CLI](/api/clis/create-dagster) (recommended), manually create a new project, or update an existing project to install Dagster dependencies.

- [Installation requirements for using the `create-dagster` CLI](#installation-requirements-for-using-the-create-dagster-cli)
- [Installation requirements for manually creating or updating a project](#installation-requirements-for-manually-creating-or-updating-a-project)

## Installation requirements for using the `create-dagster` CLI

If you're just getting started with Dagster, we recommend scaffolding a new project with the `create-dagster` command line utility, which will generate a Dagster project with our recommended structure and required dependencies.

<Tabs>
<TabItem value="uv" label="uv (Recommended)">

Install the Python package manager [`uv`](https://docs.astral.sh/uv/getting-started/installation):

<InstallUv />

Installing `uv` will install the [`uvx` command](https://docs.astral.sh/uv/guides/tools), which allows you to execute commands without having to install packages directly. You can run the `create-dagster` command using `uvx`:

<CliInvocationExample contents="uvx create-dagster@latest project my-project" />

</TabItem>

<TabItem value="brew" label="Homebrew">

The `create-dagster` command line utility is available in a Homebrew tap:

<CliInvocationExample contents="brew install dagster-io/tap/create-dagster" />

After installation, you can run the `create-dagster` command:

<CliInvocationExample contents="create-dagster project my-project" />

</TabItem>

<TabItem value="curl" label="curl">

Use `curl` to download a standalone installation script for the `create-dagster` command line utility and execute it with `sh`:

<CliInvocationExample contents="curl -LsSf https://dg.dagster.io/create-dagster/install.sh | sh" />

After installation, you can run the `create-dagster` command:

<CliInvocationExample contents="create-dagster project my-project" />

</TabItem>

</Tabs>

## Installation requirements for manually creating or updating a project

If you prefer to set up Dagster manually or are installing it into an existing project, you can install Dagster directly into your Python environment:

<Tabs>
  <TabItem value="uv" label="uv">
    <CliInvocationExample contents="uv add dagster dagster-webserver dagster-dg-cli" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample contents="pip install dagster dagster-webserver dagster-dg-cli" />
  </TabItem>
</Tabs>

## Verifying your Dagster installation

To verify that Dagster is installed correctly, run the commands below. You should see the version number of `dg` in your environment.

<Tabs groupId="os">
  <TabItem value="mac" label="Mac">
    <CliInvocationExample contents="cd my-project" />
    <CliInvocationExample contents="source .venv/bin/activate" />
    <CliInvocationExample contents="dg --version" />
  </TabItem>
  <TabItem value="windows" label="Windows">
    <CliInvocationExample contents="cd my-project" />
    <CliInvocationExample contents=".venv\Scripts\activate" />
    <CliInvocationExample contents="dg --version" />
  </TabItem>
  <TabItem value="linux" label="Linux">
    <CliInvocationExample contents="cd my-project" />
    <CliInvocationExample contents="source .venv/bin/activate" />
    <CliInvocationExample contents="dg --version" />
  </TabItem>
</Tabs>

## Troubleshooting

If you run into trouble during the installation process, reach out to the [Dagster community](/about/community).

## Next steps

- Follow the [Quickstart](/getting-started/quickstart) to get up and running with a basic Dagster project
- Follow the [Tutorial](/dagster-basics-tutorial) to learn how to build a more complex ETL pipeline
- Add [assets](/guides/build/assets/defining-assets) to your Dagster project
