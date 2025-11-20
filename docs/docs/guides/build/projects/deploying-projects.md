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

### Dagster+ Serverless production deployment

Get started with [Dagster+ Serverless](/deployment/dagster-plus/getting-started), if you haven't already. You will be guided through the process of creating a project that contains a CI/CD workflow file, which is used to configure continuous deployment of your project.

If you are deploying an additional project to an existing Dagster+ Serverless deployment, you will need to create the CI/CD workflow file yourself.

For more information, see the [Dagster+ Serverless CI/CD guide](/deployment/dagster-plus/deploying-code/ci-cd/ci-cd-in-serverless).

### Dagster+ Hybrid production deployment

Get started with [Dagster+ Hybrid](/deployment/dagster-plus/getting-started), if you haven't already, then follow the steps below to generate configuration files for your use case.

<Tabs>
   <TabItem value="github" label="CI/CD with GitHub">
   1. Change to the project directory:
      ```shell
      cd my-project
      ```
   2. Initialize a Git repository:
      ```shell
      git init .
      ```
   3. Use the `dg` CLI to scaffold deployment configuration files:
      ```shell
      dg plus deploy configure hybrid --git-provider github
      ```
   4. Update the `build.yaml` file with your Docker registry.
   
   :::info

   The `dg plus deploy configure hybrid --git-provider github` command will create the following deployment configuration files:

      - A Dockerfile
      - A `build.yaml` configuration file
      - A `.github/dagster-cloud-deploy.yml` GitHub Action workflow configuration file.
   ::: 
   </TabItem>
   <TabItem value="gitlab" label="CI/CD with GitLab">
   1. Change to the project directory:
      ```shell
      cd my-project
      ```
   2. Initialize a Git repository:
      ```shell
      git init .
      ```
   3. Use the `dg` CLI to scaffold deployment configuration files:
      ```shell
      dg plus deploy configure hybrid --git-provider gitlab
      ```
   4. Update the `build.yaml` file with your Docker registry.
   
   :::info

   The `dg plus deploy configure hybrid --git-provider gitlab` command will create the following deployment configuration files:

      - A Dockerfile
      - A `build.yaml` configuration file
      - A `.gitlab-ci.yml` GitLab CI/CD configuration file.
   ::: 
   </TabItem>
   <TabItem value="non-github" label="CI/CD with a non-GitHub provider">
   1. Change to the project directory:
      ```shell
      cd my-project
      ```
   2. Initialize a Git repository:
      ```shell
      git init .
      ```
   3. Use the `dg` CLI to scaffold deployment configuration files:
      ```shell
      dg plus deploy configure hybrid
      ```
   4. Update the `build.yaml` file with your Docker registry.
   5. To configure CI/CD, follow the steps in the ["Non-GitHub CI/CD provider" section of CI/CD in Dagster+ Hybrid guide](/deployment/dagster-plus/deploying-code/ci-cd/ci-cd-in-hybrid#non-github).
   
   :::info

   The `dg plus deploy configure hybrid` command will create the following deployment configuration files:

      - A Dockerfile
      - A `build.yaml` configuration file
   ::: 
   </TabItem>
</Tabs>
