---
title: "Dagster installation"
description: "Learn how to install Dagster"
---

# Dagster installation

This guide will walk you through the steps to install Dagster, a data orchestrator for machine learning, analytics, and ETL. Follow the instructions below to get started with Dagster on your local machine.

<details>
  <summary>Prerequisites</summary>

Before you begin, ensure you have the following prerequisites installed on your system:

- Python 3.7 or higher, Python 3.11 is recommended
- pip, a Python package installer

</details>

## Set up a virtual environment

After installing Python, it's a good idea to setup a virtual environment to isolate your Dagster project from the rest of your system.

There are many ways to setup a virtual environment. One method that requires no
additional dependencies is to use `venv`.

```bash
python -m venv .venv
source .venv/bin/activate
```

`pyenv` and `pyenv-virtualenv` are more powerful tools that can help you manage multiple versions of Python on a single machine. You can learn more about them in the [pyenv GitHub repository](https://github.com/pyenv/pyenv).

## Install Dagster

To install Dagster in your virtual environment, open your terminal and run the following command:

```bash
pip install dagster dagster-webserver
```

This command will install the core Dagster library and the webserver, which is used to serve the Dagster UI.

## Verify installation

To verify that Dagster is installed correctly, you can run the following command:

```bash
dagster --version
```

You should see the version numbers of Dagster printed in the terminal.

```bash
> dagster --version
dagster, version 1.7.6
```

If you see `dagster, version 1!0+dev`, then you have the development version of Dagster
installed. You can choose to install the latest stable version by providing a version
to the `pip install` command.

For example, to install version 1.7.6, you can run:

```bash
pip install 'dagster==1.7.6'
```

## Conclusion

Congratulations! You have successfully installed Dagster

## Troubleshooting

If you encounter any issues during the installation process, refer to the [Dagster GitHub repository](https://github.com/dagster-io/dagster) for troubleshooting or reach out to the Dagster community for further assistance.

## Next steps

- [Quickstart Tutorial](/tutorial/quick-start)
- [ETL Tutorial](/tutorial/tutorial-etl)
- [Create a new Dagster project](/tutorial/create-new-project)
- [Creating Data Assets](/guides/data-assets)
