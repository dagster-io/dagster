---
title: "Creating a new Dagster project"
description: Dagster comes with a convenient CLI command for creating a new project. This guide explains the role of each generated file and directory.
sidebar_position: 100
---

The easiest way to start building a Dagster project is by using the `dagster project` CLI. This CLI tool helps generate files and folder structures that enable you to quickly get started with Dagster.


## Step 1: Bootstrap a new project

:::note

  If you don't already have Dagster installed, verify you meet the{" "}
  <a href="/getting-started/install">installation requirements</a> before
  continuing.

:::

You can scaffold a new project using the default project skeleton, or start with one of the official Dagster examples.

To learn more about the default files in a Dagster project, refer to the [Dagster project file reference](dagster-project-file-reference).

<Tabs>
<TabItem value="Default project skeleton">

### Using the default project skeleton

To get started, run:

```bash
pip install dagster
dagster project scaffold --name my-dagster-project
```

The `dagster project scaffold` command generates a folder structure with a single Dagster code location and other files, such as `pyproject.toml` and `setup.py`. This takes care of setting things up with an empty project, enabling you to quickly get started.

</TabItem>
<TabItem value="Official example">

### Using an official example

To get started using an official Dagster example, run:

```bash
pip install dagster
dagster project from-example \
  --name my-dagster-project \
  --example quickstart_etl
```

The command `dagster project from-example` downloads one of the official Dagster examples to the current directory. This command enables you to quickly bootstrap your project with an officially maintained example.

For more info about the examples, visit the [Dagster GitHub repository](https://github.com/dagster-io/dagster/tree/master/examples) or use `dagster project list-examples`.

</TabItem>
</Tabs>

## Step 2: Install project dependencies

The newly generated `my-dagster-project` directory is a fully functioning [Python package](https://docs.python.org/3/tutorial/modules.html#packages) and can be installed with `pip`.

To install it as a package and its Python dependencies, run:

```bash
pip install -e ".[dev]"
```

:::

  Using the <code>--editable</code> (<code>-e</code>) flag instructs{" "}
  <code>pip</code> to install your code location as a Python package in{" "}
  <a href="https://pip.pypa.io/en/latest/topics/local-project-installs/#editable-installs">
    "editable mode"
  </a>{" "}
  so that as you develop, local code changes are automatically applied.

:::

## Step 3: Start the Dagster UI

To start the [Dagster UI](/guides/operate/webserver), run:

```bash
dagster dev
```

**Note**: This command also starts the [Dagster daemon](/guides/deploy/execution/dagster-daemon). Refer to the [Running Dagster locally guide](/guides/deploy/deployment-options/running-dagster-locally) for more info.

Use your browser to open [http://localhost:3000](http://localhost:3000) to view the project.

## Step 4: Development

- [Adding new Python dependencies](#adding-new-python-dependencies)
- [Environment variables and secrets](#using-environment-variables-and-secrets)
- [Unit testing](#adding-and-running-unit-tests)

### Adding new Python dependencies

You can specify new Python dependencies in `setup.py`.

### Using environment variables and secrets

Environment variables, which are key-value pairs configured outside your source code, allow you to dynamically modify application behavior depending on environment.

Using environment variables, you can define various configuration options for your Dagster application and securely set up secrets. For example, instead of hard-coding database credentials - which is bad practice and cumbersome for development - you can use environment variables to supply user details. This allows you to parameterize your pipeline without modifying code or insecurely storing sensitive data.

For more information and examples, see "[Using environment variables and secrets](/guides/deploy/using-environment-variables-and-secrets)".

### Adding and running unit tests

Tests can be added in the `my_dagster_project_tests` directory and run using `pytest`:

```bash
pytest my_dagster_project_tests
```

## Next steps

Once your project is ready to move to production, check out our recommendations for [transitioning data pipelines from development to production](/guides/deploy/dev-to-prod).

Check out the following resources to learn more about deployment options:

- [Dagster+](/dagster-plus/) - Deploy using Dagster-managed infrastructure
- [Your own infrastructure](/guides/deploy/) - Deploy to your infrastructure, such as Docker, Kubernetes, Amazon Web Services, etc.
