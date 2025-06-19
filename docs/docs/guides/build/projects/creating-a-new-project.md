---
title: "Creating a new Dagster project"
description: dg allows you to create a special type of Python package, called a project, that defines a Dagster code location.
sidebar_position: 100
---

The easiest way to start building a Dagster project is by using the [`create-dagster` CLI](/api/dg/create-dagster). This CLI tool allows you to create a special type of Python package, called a _project_, that defines a [Dagster code location](/deployment/code-locations/managing-code-locations-with-definitions).

## Prerequisites

Before creating a Dagster project, you must do one of the following:

* Install `uv` (recommended)
* If not using `uv`, install the `create-dagster` CLI with Homebrew or `curl`

For more information, see the [Installation doc](/getting-started/installation).

## 1. Create a project with the `create-dagster` CLI

<Tabs>
  <TabItem value="uv" label="uv">
  If you are using `uv`, you can run `create-dagster` with [`uvx`](https://docs.astral.sh/uv/guides/tools/):

  ```
  uvx -U create-dagster project my-project
  ```

  </TabItem>
  <TabItem value="non-uv" label="Homebrew or curl">

  If you are not using `uv`, you must install `create-dagster` with Homebrew, `curl`, or `pip`, then run the following command:

  ```
  create-dagster project my-project
  ```
  </TabItem>
</Tabs>

The `create-dagster project` command creates a directory with a standard Python package structure with some additions. For more information on the files and directories in a Dagster project, see the [Dagster project file reference](/guides/build/projects/dagster-project-file-reference).

## 3. Add assets

Assets are the core abstraction in Dagster and can represent logical units of data such as tables, datasets, or machine learning models. Assets can have dependencies on other assets, forming the data lineage for your pipelines. To add assets to your project, see [Defining assets](/guides/build/assets/defining-assets).

## 4: View assets in the UI

To start the [Dagster UI](/guides/operate/webserver), run:

```bash
dg dev
```

To see your assets, navigate to [http://localhost:3000](http://localhost:3000).

## Step 4: Continue development

- [Adding new Python dependencies](#add-new-python-dependencies)
- [Use environment variables and secrets](#use-environment-variables-and-secrets)
- [Add and run unit tests](#add-and-run-unit-tests)

### Add new Python dependencies

You can specify new Python dependencies in `pyproject.toml`.

### Use environment variables and secrets

Environment variables, which are key-value pairs configured outside your source code, allow you to dynamically modify application behavior depending on environment.

Using environment variables, you can define various configuration options for your Dagster application and securely set up secrets. For example, instead of hard-coding database credentials - which is bad practice and cumbersome for development - you can use environment variables to supply user details. This allows you to parameterize your pipeline without modifying code or insecurely storing sensitive data.

For more information and examples, see [Using environment variables and secrets](/guides/operate/configuration/using-environment-variables-and-secrets).

### Add and run unit tests

Tests can be added to the `tests` directory and run using `pytest`:

```bash
pytest tests
```

For more information on testing, see the following docs:
* The [Testing guides](/guides/test) for help with asset checks, data freshness checks, unit testing assets and ops, and testing partitioned config and jobs
* [Testing component definitions](/guides/build/components/building-pipelines-with-components/testing-component-definitions) if you have scaffolded definitions from an existing component
* [Testing your component](/guides/build/components/creating-new-components/testing-your-component) if you have created a custom component

## Next steps

{/* TODO make this visible once the dev to prod guide is updated: Once your project is ready to move to production, check out our recommendations for [transitioning data pipelines from development to production](/guides/operate/dev-to-prod). */}

* Add [integrations](/integrations/libraries) to your project
* Create your own [Dagster Components](/guides/build/components/creating-new-components) to share with your team
* Deploy your project to [Dagster+](/deployment/dagster-plus) or [your own infrastructure](/deployment/oss)
