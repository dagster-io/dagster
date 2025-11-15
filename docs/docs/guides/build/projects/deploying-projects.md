---
title: Deploying Dagster projects
description: How to deploy Dagster projects locally, to an OSS production deployment, and to Dagster+ Serverless or Hybrid.
sidebar_position: 200
---

## Local deployment

When run locally, Dagster can load a [project](/guides/build/projects/creating-projects) without additional configuration:

```shell
dg dev
```

This command loads the definitions in the project in the current Python environment.

For more information about local development, including how to configure your local instance, see [Running Dagster locally](/deployment/oss/deployment-options/running-dagster-locally).

:::tip Creating a workspace to manage multiple projects

To deploy more than one Dagster project, use the `dagster-create workspace` command to [create a workspace](/guides/build/projects/workspaces/creating-workspaces) to contain the projects.

:::

## Production deployment

### Open source production deployment

Follow the steps in the [OSS deployment docs](/deployment/oss/deployment-options) to set up a production OSS deployment. You will need to add your project code to the Docker container used in the deployment.

### Dagster+ production deployment

<Tabs>
<TabItem value="serverless" label="Serverless">

Get started with [Dagster+ Serverless](/deployment/dagster-plus/getting-started), if you haven't already. You will be guided through the process of creating a project that contains a CI/CD workflow file, which is used to configure continuous deployment of your project.

If you are deploying another project to an existing Dagster+ Serverless deployment, you will need to create the CI/CD workflow file yourself. For more information, see the [Dagster+ Serverless CI/CD guide](/deployment/dagster-plus/deploying-code/ci-cd/ci-cd-in-serverless).

</TabItem>
<TabItem value="hybrid" label="Hybrid">

TK - update link to `dg plus deploy configure`

1. Get started with [Dagster+ Hybrid](/deployment/dagster-plus/getting-started), if you haven't already.
2. In the root directory of your project, run [`dg plus deploy configure`](/api/clis/dg-cli/dg-plus#deploy) to create a `build.yaml` deployment configuration file and a Dockerfile. You will need to update the `build.yaml` file with your Docker registry.
3. To deploy to the cloud, you can either:
   - Perform a one-time deployment with the [`dg plus deploy`](/api/clis/dg-cli/dg-plus#deploy) command
   - [Configure CI/CD](/deployment/dagster-plus/deploying-code/ci-cd/ci-cd-in-hybrid) for continuous deployment.

</TabItem>
</Tabs>

