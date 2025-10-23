---
title: Creating and deploying Dagster projects
description: dg allows you to create a special type of Python package, called a project, that defines a Dagster code location.
sidebar_position: 100
---

The easiest way to start building a Dagster project is by using the [`create-dagster` CLI](/api/clis/create-dagster). This CLI tool allows you to create a special type of Python package, called a _project_, that defines a [Dagster code location](/guides/build/projects#code-location.

import ProjectCreationPrereqs from '@site/docs/partials/\_ProjectCreationPrereqs.md';

<ProjectCreationPrereqs />

## Step 1. Scaffold a new Dagster project

<Tabs groupId="package-manager">
   <TabItem value="uv" label="uv">
   1. Open your terminal and scaffold a new Dagster project. You can replace `my-project` with a different project name if you wish:

      ```shell
      uvx create-dagster@latest project my-project
      ```
   
   2. Respond `y` to the prompt to run `uv sync` after scaffolding

      ![Responding y to uv sync prompt](/images/getting-started/quickstart/uv_sync_yes.png)

   3. Change to the project directory:

      ```shell
      cd my-project
      ```
   4. Activate the virtual environment:

    <Tabs>
      <TabItem value="macos" label="MacOS/Unix">
        ```
        source .venv/bin/activate
        ```
      </TabItem>
      <TabItem value="windows" label="Windows">
        ```
        .venv\Scripts\activate
        ```
      </TabItem>
    </Tabs>
   </TabItem>
   <TabItem value="pip" label="pip">
   1. Open your terminal and scaffold a new Dagster project. You can replace `my-project` with a different project name if you wish:

      ```shell
      create-dagster project my-project
      ```
   2. Change to the project directory:

      ```shell
      cd my-project
      ```
   
   3. Create and activate a virtual environment:

   <Tabs>
     <TabItem value="macos" label="MacOS/Unix">
      ```shell
      python -m venv .venv
      ```
      ```shell
      source .venv/bin/activate
      ```
     </TabItem>
     <TabItem value="windows" label="Windows">
      ```shell
      python -m venv .venv
      ```
      ```shell
      .venv\Scripts\activate
      ```
     </TabItem>
   </Tabs>
   
   4. Install your project as an editable package:

      ```shell
      pip install --editable .
      ```
   </TabItem>
</Tabs>

Your new Dagster project should have the following structure:

<Tabs groupId="package-manager">

   <TabItem value="uv" label="uv">
   ```shell
   .
   └── my-project
      ├── pyproject.toml
      ├── src
      │   └── my_project
      │       ├── __init__.py
      │       ├── definitions.py
      │       └── defs
      │           └── __init__.py
      ├── tests
      │   └── __init__.py
      └── uv.lock
   ```
   </TabItem>
   <TabItem value="pip" label="pip">
   ```shell
   .
   └── my-project
      ├── pyproject.toml
      ├── src
      │   └── my_project
      │       ├── __init__.py
      │       ├── definitions.py
      │       └── defs
      │           └── __init__.py
      └── tests
         └── __init__.py
   ```
   </TabItem>
</Tabs>

:::info

The `create-dagster project` command creates a directory with a standard Python package structure with some additions. For more information on the files and directories in a Dagster project, see the [Dagster project file reference](/guides/build/projects/dagster-project-file-reference).

:::

## Step 2. Add assets

Assets are the core abstraction in Dagster and can represent logical units of data such as tables, datasets, or machine learning models. Assets can have dependencies on other assets, forming the data lineage for your pipelines. To add assets to your project, see [Defining assets](/guides/build/assets/defining-assets).

## Step 3: View assets in the UI

To start the [Dagster UI](/guides/operate/webserver), run:

```bash
dg dev
```

To see your assets, navigate to [http://localhost:3000](http://localhost:3000).

## Step 4: Continue development

- [Add new Python dependencies](#add-new-python-dependencies)
- [Add integrations](#add-integrations)
- [Use environment variables and secrets](#use-environment-variables-and-secrets)
- [Add and run unit tests](#add-and-run-unit-tests)
- [Create custom components](#create-custom-components)

### Add new Python dependencies

You can specify new Python dependencies in `pyproject.toml`.

### Add integrations

See the [Integrations docs](/integrations/libraries) for a full list of Dagster-supported and community-supported integrations.

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
* The [Testing guides](/guides/test) have guidance on asset checks, data freshness checks, unit testing assets and ops, and testing partitioned config and jobs.
* [Testing component definitions](/guides/build/components/building-pipelines-with-components/testing-component-definitions) contains testing best practices for definitions scaffolded existing components.
* [Testing your component](/guides/build/components/creating-new-components/testing-your-component) has best practices for testing custom components.

### Create custom components

If built-in Dagster components and integrations don't meet your needs, you can [create custom components](/guides/build/components/creating-new-components) to share with your team.

## Step 5: Deploy your project to the cloud (Optional)

If you have a cloud deployment of Dagster, you can deploy your project by adding a configuration file at the root, and optionally configuring CI/CD for continuous deployment.

<Tabs>
   <TabItem value="oss" label="OSS deployment">
   To deploy your project to the OSS cloud:
   - Deploy Dagster to one of the platforms listed in the [OSS deployment docs](/deployment/oss/deployment-options)
   - Add a [`dg.toml` file](/guides/build/projects/deployment-configuration/dg-toml) to your project. This file tells Dagster where to find your code and how to load it.
   </TabItem>
   <TabItem value="plus" label="Dagster+ deployment">
   To deploy to Dagster+:
   - [Get started with Dagster+ Serverless or Hybrid](/deployment/dagster-plus/getting-started), if you haven't already
   - Add a `dagster_cloud.yaml` file to the root directory of to your project
   - For one-time deployment from the command line, you can use the `dagster-cloud` CLI command line tool. For continuous deployment from GitHub, GitLab, or another Git provider, follow the steps in the CI/CD docs.
   </TabItem>
</Tabs>


## Deploying code locations

<Tabs>
<TabItem value="local" label="Local development">

When run locally, Dagster can load a project directly as a code location without additional configuration:

```shell
dg dev
```

This command loads the definitions in the project as a code location in the current Python environment.

Fore more information about local development, including how to configure your local instance, see [Running Dagster locally](/deployment/oss/deployment-options/running-dagster-locally).

</TabItem>
<TabItem value="dagster-plus" label="Dagster+ deployment">

See the [Dagster+ code locations documentation](/guides/build/projects).

</TabItem>
<TabItem value="oss" label="Open source deployment">

The `workspace.yaml` file is used to load code locations for open source (OSS) deployments. This file specifies how to load a collection of code locations and is typically used in advanced use cases. For more information, see "[workspace.yaml reference](/guides/build/projects/deployment-configuration/workspace-yaml)".

</TabItem>
</Tabs>