---
title: "Creating a new Dagster project"
description: dg allows you to create a special type of Python package, called a project, that defines a Dagster code location.
sidebar_position: 100
---

The easiest way to start building a Dagster project is by using the [`create-dagster` CLI](/api/dg/create-dagster). This CLI tool allows you to create a special type of Python package, called a _project_, that defines a [Dagster code location](/deployment/code-locations/managing-code-locations-with-definitions).

## Prerequisites

Before creating a Dagster project, you must do one of the following:

* Install `uv` (recommended)
* If not using `uv`, install the `create-dagster` CLI with Homebrew, `curl`, or `pip`

For more information, see the [Installation doc](/getting-started/installation).

## 1. Create a project with the `create-dagster` CLI

<Tabs>
  <TabItem value="uv" label="uv">
  If you are using `uv`, you can run `create-dagster` with `uvx`:

  ```
  uvx -U create-dagster project my-project
  ```

  :::tip

  `uvx` invokes a tool without installing it. For more information, see the [`uv` docs](https://docs.astral.sh/uv/guides/tools/).

  :::

  </TabItem>
  <TabItem value="non-uv" label="Homebrew, curl, or pip">

  If you are not using `uv`, you must install `create-dagster` with Homebrew, `curl`, or `pip`, then run the following command:

  ```
  create-dagster project my-project
  ```
  </TabItem>
</Tabs>

### Project structure

The `create-dagster project` command creates a directory with a standard Python package structure with some additions:

<Tabs groupId="package-manager">
  <TabItem value="uv" label="uv">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/3-uv-tree.txt" />
  </TabItem>
  <TabItem value="pip" label="pip">
    <CliInvocationExample path="docs_snippets/docs_snippets/guides/components/index/3-pip-tree.txt" />
  </TabItem>
</Tabs>

:::tip

To use `tree`, install it with `brew install tree` (Mac), or follow the [installation instructions](https://oldmanprogrammer.net/source.php?dir=projects/tree/INSTALL).

:::

- The Python package `my_project` lives in `src/my_project` and contains the deployable code that defines your Dagster pipelines.
- `my_project/defs` will contain your Dagster definitions.
- `my_project/components` is where you will define custom components, and optionally other code you wish to share across Dagster definitions.
- `my_project/definitions.py` is the entry point that Dagster will load when deploying your code location. It is configured to load all definitions from `my_project/defs`. You should not need to modify this file.
- `tests` is a separate Python package defined at the top level (outside `src`). It should contain tests for the `my_project` package.
- `pyproject.toml` is a standard Python package configuration file. In addition to the regular Python package metadata, it contains a `tool.dg` section for `dg`-specific settings.

## TK - Install project dependencies

TK

## 3. Add assets

Assets are the core abstraction in Dagster and can represent logical units of data such as tables, datasets, or machine learning models. Assets can have dependencies on other assets, forming the data lineage for your pipelines.

To add assets to your project, see [Defining assets](/guides/build/assets/defining-assets).

## 4: View assets in the UI

To start the [Dagster UI](/guides/operate/webserver), run:

```bash
dg dev
```

To see your assets, navigate to [http://localhost:3000](http://localhost:3000).

## Step 4: Continue development

- [Adding new Python dependencies](#adding-new-python-dependencies)
- [Environment variables and secrets](#using-environment-variables-and-secrets)
- [Unit testing](#adding-and-running-unit-tests)

### Adding new Python dependencies

You can specify new Python dependencies in `pyproject.toml`.

### Using environment variables and secrets

Environment variables, which are key-value pairs configured outside your source code, allow you to dynamically modify application behavior depending on environment.

Using environment variables, you can define various configuration options for your Dagster application and securely set up secrets. For example, instead of hard-coding database credentials - which is bad practice and cumbersome for development - you can use environment variables to supply user details. This allows you to parameterize your pipeline without modifying code or insecurely storing sensitive data.

For more information and examples, see [Using environment variables and secrets](/guides/operate/configuration/using-environment-variables-and-secrets).

### Adding and running unit tests

Tests can be added to the `tests` directory and run using `pytest`:

```bash
pytest my_dagster_project_tests
```

## Next steps

{/* TODO make this visible once the dev to prod guide is updated: Once your project is ready to move to production, check out our recommendations for [transitioning data pipelines from development to production](/guides/operate/dev-to-prod). */}

* Add integrations to your project
* Create your own [Dagster Components](/guides/build/components/creating-new-components) to share with your team
* Deploy your project to [Dagster+](/deployment/dagster-plus) or [your own infrastructure](/deployment/oss)
