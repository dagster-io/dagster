---
title: Running Dagster locally
description: How to run Dagster on your local machine.
---

# Running Dagster locally

In this guide, we'll walk you through how to run Dagster on your local machine using the `dagster dev` command.  The `dagster dev` command launches the Dagster UI and the Dagster daemon, allowing you to start a full deployment of Dagster from the command line.

:::warning
`dagster dev` is intended for local development _only_. If you want to run Dagster for production use cases, see our [Deployment](/guides/deployment) guides.
:::

## Locating your code

Before starting local development, you need to tell Dagster how to find the Python code containing your assets and jobs.

For a refresher on how to set up a Dagster project, follow our [Recommended Dagster Project Structure](/todo) guide.

<Tabs>
  <TabItem value="module" label="From a module">
    Dagster can load Python modules as code locations.
    <CodeExample filePath="guides/tbd/definitions.py" language="python" title="my_module/__init__.py" />
    We can use the `-m` argument to supply the name of the module to start a Dagster instance loaded with our definitions:
    ```shell
    dagster dev -m my_module
    ```

  </TabItem>
  <TabItem value="without-args" label="Without command line arguments">
    To load definitions from a module without supplying the `-m` command line argument, you can use a `pyproject.toml` file. This file, included in all Dagster example projects, contains a `tool.dagster` section where you can supply the `module_name`:
    <CodeExample filePath="guides/tbd/pyproject.toml" language="toml" title="pyproject.toml" />


  </TabItem>
  <TabItem value="file" label="From a file">
    Dagster can load a file directly as a code location.
    <CodeExample filePath="guides/tbd/definitions.py" language="python" title="definitions.py" />
    Given the preceding file, we can use the `-f` argument to supply the name of the file to start a Dagster instance loaded with our definitions:
    ```shell
    dagster dev -f defs.py
    ```

    :::note
    We don't recommend using the `-f` argument for production deployments, to avoid a whole class of Python import errors.
    :::

  </TabItem>
</Tabs>

## Creating a persistent instance

Running `dagster dev` without any additional configuration starts an ephemeral instance in a temporary directory.  You may see log output indicating as such:
```shell
Using temporary directory /Users/rhendricks/tmpqs_fk8_5 for storage.
```
This indicates that any runs or materialized assets created during your session won't be persisted once the session ends.

To designate a more permanent home for your runs and assets, you can set the `DAGSTER_HOME` environment variable to a folder on your filesystem. Dagster will then use the specified folder for storage on all subsequent runs of `dagster dev`.

```shell
mkdir -p ~/.dagster_home
export DAGSTER_HOME=~/.dagster_home
dagster dev
```

## Configuring your instance

To configure your Dagster instance, you can create a `dagster.yaml` file in your `$DAGSTER_HOME` folder.

For example, to have your local instance limit the number of concurrent runs, you could configure the following `dagster.yaml`:
    <CodeExample filePath="guides/tbd/dagster.yaml" language="yaml" title="~/.dagster_home/dagster.yaml" />


For the full list of options that can be set in the `dagster.yaml` file, refer to the [Dagster instance documentation](/todo).

