---
title: 'Running Dagster locally'
sidebar_label: Local deployment
description: How to run open source Dagster on your local machine.
sidebar_position: 1000
---

In this guide, we'll walk you through how to run Dagster on your local machine using the `dg dev` command. The `dg dev` command launches the Dagster UI and the Dagster daemon, allowing you to start a full deployment of Dagster from the command line.

:::warning

`dg dev` is intended for local development _only_. If you want to run Dagster for production use cases, see our other [OSS deployment guides](/deployment/oss/deployment-options) or check out [Dagster+](/deployment/dagster-plus).

:::

## Locating your code

Before starting local development, you need to tell Dagster how to find the Python code containing your assets and jobs.

For a refresher on how to set up a Dagster project, follow our [Recommended Dagster Project Structure](/guides/build/projects/structuring-your-dagster-project) guide.

<CodeExample
  path="docs_snippets/docs_snippets/guides/tbd/definitions.py"
  language="python"
  title="src/my_project/assets.py"
/>

```shell
dg dev
```

## Creating a persistent instance

Running `dg dev` starts an ephemeral instance in a temporary directory. You may see log output indicating as such:

```shell
...
Using temporary directory /<your path>/.tmp_dagster_home_<uuid> for storage. This will be removed when dagster dev exits.
```

This indicates that any runs or materialized assets created during your session won't be persisted once the session ends.

To designate a more permanent home for your runs and assets, you can set the `DAGSTER_HOME` environment variable to a folder on your filesystem. Dagster will then use the specified folder for storage on all subsequent runs of `dg dev`.

```shell
mkdir -p ~/.dagster_home
export DAGSTER_HOME=~/.dagster_home
dg dev
```

## Configuring your instance

To configure your Dagster instance, you can create a `dagster.yaml` file in your `$DAGSTER_HOME` folder.

For example, to have your local instance limit the number of concurrent runs, you could configure the following `dagster.yaml`:

<CodeExample
  path="docs_snippets/docs_snippets/guides/tbd/dagster.yaml"
  language="yaml"
  title="~/.dagster_home/dagster.yaml"
/>

For the full list of options that can be set in the `dagster.yaml` file, refer to the [Dagster instance documentation](/deployment/oss/oss-instance-configuration).

## Detecting when you're running in `dg dev`

You may want to detect whether you're running locally. For example, you might want schedules or sensors to start in the `RUNNING` state in production but not in your local test deployment.

`dg dev` sets the environment variable `DAGSTER_IS_DEV_CLI` to `1`. You can detect whether you're in a local dev environment by checking for the presence of that environment variable.

```python
import os

if os.getenv("DAGSTER_IS_DEV_CLI"):
    print("Running in local dev environment")
```

## Moving to production

`dg dev` is primarily useful for running Dagster for local development and testing. It isn't suitable for the demands of most production deployments. Most importantly, `dg dev` does not include authentication or web security. Additionally, in a production deployment, you might want to run multiple webserver replicas, have zero downtime continuous deployment of your code, or set up your Dagster daemon to automatically restart if it crashes.

For information about deploying Dagster in production, see the [Dagster Open Source deployment options documentation](/deployment/oss/deployment-options).
