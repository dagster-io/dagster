---
title: Deploying Dagster projects
description: How to deploy Dagster projects locally, to an OSS production deployment, and to Dagster+ Serverless or Hybrid.
sidebar_position: 200
---

## Local deployment

When run locally, Dagster can load a project directly without additional configuration:

```shell
dg dev
```

This command loads the definitions in the project in the current Python environment.

Fore more information about local development, including how to configure your local instance, see [Running Dagster locally](/deployment/oss/deployment-options/running-dagster-locally).

## Open source deployment

Follow the steps in the [OSS deployment docs](/deployment/oss/deployment-options) to set up a production OSS deployment. You will need to add your project code to the Docker container used in the deployment.

To deploy more than one Dagster project, create a [workspace](/guides/build/projects/managing-multiple-projects) to contain the projects and add a `dg.toml` file to the root of the workspace. This file tells Dagster where to find your code and how to load it.

## Dagster+ deployment

To deploy to Dagster+:

[Get started with Dagster+ Serverless or Hybrid](/deployment/dagster-plus/getting-started), if you haven't already.

<Tabs>
<TabItem value="serverless" label="Serverless">

Get started with [Dagster+ Serverless](/deployment/dagster-plus/getting-started), if you haven't already. You will be guided through the process of creating a project that contains a GitHub workflow file, which is used to configure continuous deployment of your project from a GitHub repo.

If you are deploying another project to an existing Dagster+ Serverless deployment, you will need to create the CI/CD configuration file yourself. For more information, see the [Dagster+ Serverless CI/CD guide](/deployment/deploying-code/ci-cd-in-serverless).

TK - workspace for multiple projects?

</TabItem>
<TabItem value="hybrid" label="Hybrid">

1. Get started with [Dagster+ Hybrid](/deployment/dagster-plus/getting-started), if you haven't already.
2. In the root directory of your project, run [`dg scaffold build-artifacts`](/api/clis/dg-cli/dg-cli-reference#dg-scaffold-build-artifacts) to create a `build.yaml` deployment configuration file and a Dockerfile. You will need to update the `build.yaml` file with your Docker registry.
2. To deploy to the cloud, you can either:
   - Perform a one-time deployment with the [`dagster-cloud` CLI](/api/clis/dagster-cloud-cli).
   - [Configure CI/CD](/deployment/dagster-plus/deploying-code/ci-cd/ci-cd-in-hybrid) for continuous deployment.

TK - workspace for multiple projects?

</TabItem>
</Tabs>

