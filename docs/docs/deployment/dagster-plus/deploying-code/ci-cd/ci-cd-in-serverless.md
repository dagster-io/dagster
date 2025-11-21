---
description: Implement CI/CD for your Dagster+ Serverless deployment with GitHub, GitLab, or another Git provider.
sidebar_position: 7210
title: CI/CD in Dagster+ Serverless
tags: [dagster-plus-feature]
---

:::note

This guide only applies to [Dagster+ Serverless deployments](/deployment/dagster-plus/serverless). For Hybrid guidance, see [CI/CD in Dagster+ Hybrid](/deployment/dagster-plus/deploying-code/ci-cd/ci-cd-in-hybrid).

:::

When you sign up for Dagster+ Serverless, you are guided through creating a GitHub or GitLab repository that contains basic Dagster project code and a CI/CD workflow file consistent with Dagster+ best practices.

Once you have set up your project repository, pushing changes to the `main` branch will automatically deploy them to your `prod` Serverless [full deployment](/deployment/dagster-plus/deploying-code/full-deployments). Pull or merge requests will create ephemeral [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments) that you can preview and test in the Dagster+ UI.

**To add another Dagster project to your Serverless deployment**, follow the steps below to create a GitHub or GitLab CI/CD configuration file in your project to deploy and synchronize your code to Dagster+ Serverless. You can also use other Git providers, or a local Git repository with the [dg CLI](/api/clis/) to run your own CI/CD process.

<Tabs>
  <TabItem value="github" label="GitHub">

  :::note Prerequisites

  Before following the steps in this section, you must first [create a Dagster project](/guides/build/projects/creating-projects).

  :::

  1. Change to the project directory:
    ```shell
    cd <project-directory>
    ```
  2. Initialize a Git repository:
    ```shell
    git init .
    ```
  3. Use the `dg` CLI to scaffold deployment configuration files:
    ```shell
    dg plus deploy configure serverless --git-provider github
    ```
    
  :::info

  The `dg plus deploy configure serverless --git-provider github` command will create the following deployment configuration files:

    - A Dockerfile
    - A `build.yaml` configuration file
    - A `.github/dagster-plus-deploy.yml` GitHub Action workflow configuration file.
  ::: 

  </TabItem>
  <TabItem value="gitlab" label="GitLab">

  :::note Prerequisites

  Before following the steps in this section, you must first [create a Dagster project](/guides/build/projects/creating-projects).

:::

  1. Change to the project directory:
    ```shell
    cd <project-directory>
    ```
  2. Initialize a Git repository:
    ```shell
    git init .
    ```
  3. Use the `dg` CLI to scaffold deployment configuration files:
    ```shell
    dg plus deploy configure serverless --git-provider gitlab
    ```
  4. Update the `build.yaml` file with your Docker registry.
  
  :::info

  The `dg plus deploy configure serverless --git-provider gitlab` command will create the following deployment configuration files:

    - A Dockerfile
    - A `build.yaml` configuration file
    - A `.gitlab-ci.yml` GitLab CI/CD configuration file.
  ::: 

  </TabItem>
  <TabItem value="other" label="Other Git providers or local development">

  :::note Prerequisites

  Before following the steps in this section, you must first [create a Dagster project](/guides/build/projects/creating-projects).

  :::

  If you don't want to use our automated GitHub/GitLab process, you can use the [`dagster-cloud` command-line CLI](/api/clis/dagster-cloud-cli) in another CI environment or locally.

  1. First, [create a new project with the `create-dagster project` command](/guides/build/projects/creating-projects) and activate the project virtual environment.

  2. Next, install the [`dagster-cloud` CLI](/api/clis/dagster-cloud-cli/installing-and-configuring) and use the `configure` command to authenticate it to your Dagster+ organization: TODO - replace this with `dg` equivalent

    ```shell
    pip install dagster-cloud
    dagster-cloud configure
    ```

  You can also configure the `dagster-cloud` tool non-interactively; for more information, see [the `dagster-cloud` installation and configuration docs](/api/clis/dagster-cloud-cli/installing-and-configuring). TODO - replace with `dg` equivalent

  3. Finally, deploy your project to Dagster+ using the `serverless` command:

  ```shell
  dagster-cloud serverless deploy-python-executable ./my-project \
    --location-name example \
    --package-name quickstart_etl \
    --python-version 3.12
  ```

  :::note Windows variant

  If you are using Windows, you will need to replace the `deploy-python-executable` command with `deploy`:

  ```shell
  dagster-cloud serverless deploy ./my-project \
    --location-name example \
    --package-name quickstart_etl \
    --python-version 3.12
  ```

  :::

  </TabItem>
</Tab>
