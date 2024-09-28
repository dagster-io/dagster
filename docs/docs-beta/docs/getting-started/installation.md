---
title: Installing Dagster
description: Learn how to install Dagster
sidebar_position: 20
sidebar_label: Installation
---

# Installing Dagster

To follow the steps in this guide, you'll need:

- To install Python 3.8 or higher. **Python 3.11 is recommended**.
- To install pip, a Python package installer

## Setting up a virtual environment

After installing Python, it's recommended that you set up a virtual environment. This will isolate your Dagster project from the rest of your system and make it easier to manage dependencies.

There are many ways to do this, but this guide will use `venv` as it doesn't require additional dependencies.

<Tabs>
<TabItem value="macos" label="MacOS">
```bash
python -m venv venv
source venv/bin/activate
```
</TabItem>
<TabItem value="windows" label="Windows">
```bash
python -m venv venv
source venv\Scripts\activate
```
</TabItem>
</Tabs>

:::tip
**Looking for something more powerful than `venv`?** Try `pyenv` or `pyenv-virtualenv`, which can help you manage multiple versions of Python on a single machine. Learn more in the [pyenv GitHub repository](https://github.com/pyenv/pyenv).
:::

## Installing Dagster

To install Dagster in your virtual environment, open your terminal and run the following command:

```bash
pip install dagster dagster-webserver
```

This command will install the core Dagster library and the webserver, which is used to serve the Dagster UI.

## Verifying installation

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
- Learn to [create data assets in Dagster](/guides/data-assets)
