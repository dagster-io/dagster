---
title: Deploying Dagster projects
description: Separate code locations allow you to deploy different Dagster projects that still roll up into a single Dagster+ deployment with one global lineage graph.
sidebar_position: 200
---


## Local deployment

When run locally, Dagster can load a project directly as a code location without additional configuration:

```shell
dg dev
```

This command loads the definitions in the project as a code location in the current Python environment.

Fore more information about local development, including how to configure your local instance, see [Running Dagster locally](/deployment/oss/deployment-options/running-dagster-locally).

## Open source deployment

To deploy your project to the OSS cloud:
- Deploy Dagster to one of the platforms listed in the [OSS deployment docs](/deployment/oss/deployment-options)
- Add a [`dg.toml` file](/guides/build/projects/project-structure/deployment-configuration/dg-toml) to your project. This file tells Dagster where to find your code and how to load it.

The `workspace.yaml` file is used to load code locations for open source (OSS) deployments. This file specifies how to load a collection of code locations and is typically used in advanced use cases. For more information, see "[workspace.yaml reference](/guides/build/projects/project-structure/deployment-configuration/workspace-yaml)".

## Dagster+ deployment

To deploy to Dagster+:

[Get started with Dagster+ Serverless or Hybrid](/deployment/dagster-plus/getting-started), if you haven't already.

<Tabs>
    <TabItem value="serverless" label="Serverless">
        Run `dg scaffold github-action`, which will create `.github/workflows/dagster-plus-deploy.yml`. No additional configuration file is required.
    </TabItem>
    <TabItem value="hybrid" label="Hybrid">
        Run `dg scaffold build-artifacts`, which will create a `build.yaml` deployment configuration file and a Dockerfile. You will need to update the `build.yaml` file with your Docker registry.
    </TabItem>
</Tabs>

