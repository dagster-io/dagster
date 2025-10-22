---
title: Creating and deploying code locations
description: "A code location is a collection of Dagster definitions loadable and accessible by Dagster's tools. Learn to create, load, and deploy code locations."
sidebar_position: 100
---

A code location is a collection of Dagster definitions loadable and accessible by Dagster's tools, such as the CLI, UI, and Dagster+.

## Defining code locations

To define a code location:

1. Use the [`create-dagster` CLI](/guides/build/projects/creating-a-new-project) to create a Dagster project that contains an instance of a <PyObject section="definitions" module="dagster" object="Definitions" /> object in a top-level variable.
2. Add either a [`dg.toml` file](/deployment/code-locations/configuration-code-locations/dg-toml) (OSS) or a [`dagster_cloud.yaml` file](/deployment/code-locatons/configuring-code-locations/dagster-cloud-yaml) (Dagster+) that tells Dagster how to load the project. 

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

See the [Dagster+ code locations documentation](/deployment/code-locations).

</TabItem>
<TabItem value="oss" label="Open source deployment">

The `workspace.yaml` file is used to load code locations for open source (OSS) deployments. This file specifies how to load a collection of code locations and is typically used in advanced use cases. For more information, see "[workspace.yaml reference](/deployment/code-locations/configuring-code-locations/workspace-yaml)".

</TabItem>
</Tabs>
