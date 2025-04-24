---
title: Installing Dagster
description: Learn how to install Dagster
sidebar_position: 20
sidebar_label: Installation
---

import InstallUv from '@site/docs/partials/\_InstallUv.md';

To follow the steps in this guide, you'll need:

- To install Python 3.9 or higher. **Python 3.12 is recommended**.

## Installing dg

To optimize your Dagster experience, we recommend using `dg`—a tool that streamlines the Dagster development workflow and works seamlessly with any Python package manager.

<Tabs>
<TabItem value="uv" label="uv">

First, install the Python package manager [`uv`](https://docs.astral.sh/uv/) if you don't have it:

<InstallUv />

Although you can create a virtual environment and install `dagster-dg` using `uv`, we recommend a global installation for most users. It's simpler, requires only a one-time setup, and offers better support across multiple Python projects.

</TabItem>
<TabItem value="pip" label="pip">

If you are starting a project from scratch:

```
mkdir my_project && cd my_project
```

```
python -m venv .venv && source .venv/bin/activate
```

If you're not starting a new project, simply activate your desired virtual environment:

```
pip install dagster-dg
```

</TabItem>
</Tabs>

## Verifying dg installation

To verify that `dg` is installed correctly, run the following command:

```bash
> dg --version
dg, version 0.26.11
```

## Initializing a Dagster project

Once `dg` is installed (assuming a global installation), it can manage virtual environments for your Dagster projects. To get started, open your terminal and run:

```bash
dg init my-project && cd my-project
```

<Tabs>
  <TabItem value="macos" label="MacOS">
    ```bash
    source .venv/bin/activate
    ```
  </TabItem>
  <TabItem value="windows" label="Windows">
    ```bash
    .venv\Scripts\activate
    ```
  </TabItem>
  <TabItem value="linux" label="Linux">
    ```bash
    source .venv/bin/activate
    ```
  </TabItem>
</Tabs>

This command will install the core Dagster library and the webserver, which is used to serve the Dagster UI.

## Verifying dagster installation

To confirm that Dagster is installed correctly, run the following command from within your virtual environment. You should see Dagster's version numbers printed in the terminal:

```bash
> dagster --version
dagster, version 1.10.11
```

## Troubleshooting

If you encounter any issues during the installation process:

- Refer to the [Dagster GitHub repository](https://github.com/dagster-io/dagster) for troubleshooting, or
- Reach out to the [Dagster community](/about/community)

## Next steps

- Get up and running with your first Dagster project in the [Quickstart](/getting-started/quickstart)
- Learn to [create data assets in Dagster](/guides/build/assets/defining-assets)
