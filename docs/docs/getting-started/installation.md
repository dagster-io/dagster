---
title: Installing Dagster
description: Learn how to install Dagster and create projects with the new dg CLI.
sidebar_position: 20
sidebar_label: Installation
---

import InstallUv from '@site/docs/partials/\_InstallUv.md';

To follow the steps in this guide, you'll need:

- To install Python 3.9 or higher. **Python 3.12 is recommended**.

## Recommended: Creating a new project with create-dagster

The recommended way to get started with Dagster is to create a project using the `create-dagster` command line utility. This will scaffold a Dagster project with our recommended structure, and required dependencies.

### Using `create-dagster`

The `create-dagster` utility can be installed using [Homebrew](https://brew.sh/), `curl` or invoked without installation using `uvx`.

<Tabs>
<TabItem value="uvx" label="uvx (Recommended)">

First, install the Python package manager [`uv`](https://docs.astral.sh/uv/) if you don't have it:

<InstallUv />

Then run the `create-dagster` command using `uvx`:

```bash
uvx create-dagster project my-project
```

</TabItem>

<TabItem value="brew" label="Homebrew">

`create-dagster` is available in a Homebrew tap:

```bash
brew install dagster-io/tap/create-dagster
```

Then run the `create-dagster` command:

```bash
create-dagster project my-project
```

</TabItem>

<TabItem value="curl" label="curl">

Use `curl` to download a standalone installation script and execute it with `sh`:

```bash
curl -LsSf https://dg.dagster.io/create-dagster/install.sh | sh
```

Then run the `create-dagster` command:

```bash
create-dagster project my-project
```

</TabItem>

</Tabs>

### Verifying your new project

After creating your project, navigate to the project directory, activate the Python virtual environment, and verify the installation:

```bash
cd my-project
source .venv/bin/activate
dg --version
```

## Alternative: Manual installation in a virtual environment

If you prefer to set up Dagster manually or are installing it into an existing project, you can install Dagster in a virtual environment.

### Installing Dagster

<Tabs>
<TabItem value="uv" label="uv">

```bash
uv add dagster dagster-webserver dagster-dg-cli
```

</TabItem>

<TabItem value="pip" label="pip">

```bash
pip install dagster dagster-webserver dagster-dg-cli
```

</TabItem>
</Tabs>

### Verifying installation

To verify that Dagster is installed correctly, run the following command:

```bash
dagster --version
```

The version numbers of Dagster should be printed in the terminal:

```bash
> dagster --version
dagster, version 1.8.4
```

## Troubleshooting

If you encounter any issues during the installation process:

- Refer to the [Dagster GitHub repository](https://github.com/dagster-io/dagster) for troubleshooting, or
- Reach out to the [Dagster community](/about/community)

## Next steps

- Get up and running with your first Dagster project in the [Quickstart](/getting-started/quickstart)
- Learn more about the [`dg` CLI and modern Dagster development](/guides/labs/dg)
- Learn to [create data assets in Dagster](/guides/build/assets/defining-assets)
