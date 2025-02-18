---
title: "Running Dagster locally"
sidebar_label: Local deployment
description: How to run Dagster on your local machine.
sidebar_position: 1
---

In this guide, we'll walk you through how to run Dagster on your local machine using the `dagster dev` command.  The `dagster dev` command launches the Dagster UI and the Dagster daemon, allowing you to start a full deployment of Dagster from the command line.

:::warning
`dagster dev` is intended for local development _only_. If you want to run Dagster for production use cases, see our other [deployment guides](/guides/deploy/deployment-options/index.md).
:::

## Locating your code

Before starting local development, you need to tell Dagster how to find the Python code containing your assets and jobs.

For a refresher on how to set up a Dagster project, follow our [Recommended Dagster Project Structure](/guides/build/projects/structuring-your-dagster-project) guide.

<Tabs>
  <TabItem value="module" label="From a module">
    Dagster can load Python modules as code locations.
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/tbd/definitions.py" language="python" title="my_module/__init__.py" />
    We can use the `-m` argument to supply the name of the module to start a Dagster instance loaded with our definitions:
    ```shell
    dagster dev -m my_module
    ```

  </TabItem>
  <TabItem value="without-args" label="Without command line arguments">
    To load definitions from a module without supplying the `-m` command line argument, you can use a `pyproject.toml` file. This file, included in all Dagster example projects, contains a `tool.dagster` section where you can supply the `module_name`:
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/tbd/pyproject.toml" language="toml" title="pyproject.toml" />


  </TabItem>
  <TabItem value="file" label="From a file">
    Dagster can load a file directly as a code location.
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/tbd/definitions.py" language="python" title="definitions.py" />
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
Using temporary directory /Users/rhendricks/.tmp_dagster_home_qs_fk8_5 for storage.
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
    <CodeExample path="docs_beta_snippets/docs_beta_snippets/guides/tbd/dagster.yaml" language="yaml" title="~/.dagster_home/dagster.yaml" />


For the full list of options that can be set in the `dagster.yaml` file, refer to the [Dagster instance documentation](/guides/deploy/dagster-instance-configuration).

## Detecting when you're running in `dagster dev`

You may want to detect whether you're running locally. For example, you might want schedules or sensors to start in the `RUNNING` state in production but not in your local test deployment.

`dagster dev` sets the environment variable `DAGSTER_IS_DEV_CLI` to `1`. You can detect whether you're in a local dev environment by checking for the presence of that environment variable.

## Moving to production

`dagster dev` is primarily useful for running Dagster for local development and testing. It isn't suitable for the demands of most production deployments. Most importantly, `dagster dev` does not include authentication or web security. Additionally, in a production deployment, you might want to run multiple webserver replicas, have zero downtime continuous deployment of your code, or set up your Dagster daemon to automatically restart if it crashes.

For information about deploying Dagster in production, see the [Dagster Open Source deployment options documentation](/guides/deploy/deployment-options/).
