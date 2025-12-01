---
title: Configuring CI/CD in Dagster+
sidebar_label: CI/CD
description: Implement CI/CD for your Dagster+ Serverless or Hybrid deployment with GitHub, GitLab, or another CI/CD provider.
sidebar_position: 20
tags: [dagster-plus-feature]
---

import UpdateGitHubActionVersion from '@site/docs/partials/_UpdateGitHubActionVersion.md';
import GitHubPrereqs from '@site/docs/partials/_GitHubPrereqs.md';
import GitLabPrereqs from '@site/docs/partials/_GitLabPrereqs.md';


Follow the steps below to create a GitHub or GitLab CI/CD configuration file in your project to deploy and synchronize your code to Dagster+. You can also use other Git providers, or a local Git repository to run your own CI/CD process.

:::info A note on Dagster+ Serverless

When you sign up for Dagster+ Serverless, you are guided through creating a GitHub or GitLab repository that contains basic Dagster project code and a CI/CD workflow file consistent with Dagster+ best practices.

Once you have set up your project repository, pushing changes to the `main` branch will automatically deploy them to your `prod` Serverless [full deployment](/deployment/dagster-plus/deploying-code/full-deployments). Pull or merge requests will create ephemeral [branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments) that you can preview and test in the Dagster+ UI.

**To add another Dagster project to your Serverless deployment**, follow the steps below to create a GitHub or GitLab CI/CD configuration file in your project to deploy and synchronize your code to Dagster+ Serverless. You can also use other Git providers, or a local Git repository with the [`dagster-cloud` CLI](/api/clis/dagster-cloud-cli) to run your own CI/CD process.

:::

## GitHub

<GitHubPrereqs />

1.  Change to the project root directory:

    ```shell
    cd <project-directory>
    ```

2.  If you haven't already done so, initialize a Git repository in the project directory:

    ```shell
    git init .
    ```

3.  If you haven't already done so, create a remote repository on GitHub to connect with the local project repository. Be sure to select `Push an existing local repository to github.com` when prompted:

    ```shell
    gh repo create
    ```

4.  Use the [`dg plus deploy configure` CLI](/api/clis/dg-cli/dg-plus#configure) to scaffold deployment configuration files (`build.yaml`, Dockerfile, and GitHub Actions workflow file):

    ```shell
    dg plus deploy configure --git-provider github
    ```

5.  Create a Dagster Cloud API token and set it as a GitHub Action secret for the project:

    ```shell
    dg plus create ci-api-token --description 'Used in my-project GitHub Actions' | gh secret set DAGSTER_CLOUD_API_TOKEN
    ```

6.  Commit and push your changes to deploy to Dagster Plus:

    ```shell
    git add . && git commit -m "Deploy to Dagster+" && git push origin main
    ```

During the deployment, the agent will attempt to load your code and update the metadata in Dagster+. When that has finished, you should see the GitHub Action complete successfully, and also be able to see the code location under the **Deployment** tag in Dagster+.

<UpdateGitHubActionVersion />

## GitLab

<GitLabPrereqs />

1.  Change to the project root directory:

    ```shell
    cd <project-directory>
    ```

2.  If you haven't already done so, initialize a Git repository in the project directory:

    ```shell
    git init .
    ```

3.  TODO - create remote repo on GitLab

4.  Use the [`dg plus deploy configure` CLI](/api/clis/dg-cli/dg-plus#configure) to scaffold deployment configuration files (`build.yaml`, Dockerfile, and GitLab CI/CD configuration file):

    ```shell
    dg plus deploy configure --git-provider gitlab
    ```

5.  TODO - create a Dagster Cloud API token and set it as a secret for the GitLab repo:

6.  Commit and push your changes to deploy to Dagster Plus:

    ```shell
    git add . && git commit -m "Deploy to Dagster+" && git push origin main
    ```

## Other Git providers or local development

<Tabs>
<TabItem value="serverless" label="Dagster+ Serverless">

:::info Prerequisites

Before following the steps in this section, you must first [create a Dagster project](/guides/build/projects/creating-projects).

:::

If you don't want to use our automated GitHub/GitLab process, you can use the [`dagster-cloud` command-line CLI](/api/clis/dagster-cloud-cli) in another CI environment or locally.

1. First, [create a new project with the `create-dagster project` command](/guides/build/projects/creating-projects) and activate the project virtual environment.

2. Next, install the [`dagster-cloud` CLI](/api/clis/dagster-cloud-cli/installing-and-configuring) and use the `configure` command to authenticate it to your Dagster+ organization:

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
<TabItem value="hybrid" label="Dagster+ Hybrid">

If you are using a non-GitHub CI/CD provider, your system should use the [`dg deploy` command](/api/clis/dg-cli/dg-plus#deploy) to deploy code locations to Dagster+.

{/* TODO add step 2 below for running `dg` equivalent of `dagster-cloud ci check --project-dir=. */}

1.  Set the build environment variables. Note that all variables are required:
    - `DAGSTER_CLOUD_ORGANIZATION`: The name of your organization in Dagster+.
    - `DAGSTER_CLOUD_API_TOKEN`: A Dagster+ API token. **Note:** This is a sensitive value and should be stored as a CI/CD secret if possible.
    - `DAGSTER_BUILD_STATEDIR`: A path to a blank or non-existent temporary directory on the build machine that will be used to store local state during the build.
2.  Initialize the build session:

    ```
    dg plus deploy start --deployment=DEPLOYMENT_NAME --project-dir=.
    ```

    This reads the `build.yaml` configuration and initializes the DAGSTER_BUILD_STATEDIR.

3.  Build and upload Docker images for your code locations.

    The Docker image should contain a Python environment with `dagster`, `dagster-cloud`, and your code. For reference, see the [example Dockerfile](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/blob/main/Dockerfile) in our template repository. The example uses `pip install .` to install the code including the dependencies specified in [`setup.py`](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/blob/main/setup.py).

    It is a good idea to use a unique image tag for each Docker build. You can build one image per code location or a shared image for multiple code locations. As an example image tag, you can use the git commit SHA:

    ```
    export IMAGE_TAG=`git log --format=format:%H -n 1`
    ```

    Use this tag to build and upload your Docker image, for example:

    ```
    docker build . -t ghcr.io/org/dagster-cloud-image:$IMAGE_TAG
    docker push ghcr.io/org/dagster-cloud-image:$IMAGE_TAG
    ```

    The upload step is specific to your Docker container registry and will require authentication. The only requirement is that the registry you upload to must match the registry specified in `build.yaml`.

4.  Update the build session with the Docker image tag. For each code location you want to deploy, run the following command passing the `IMAGE_TAG` used in the previous step:

    ```
    dg plus deploy set-build-output --location-name=code-location-a --image-tag=IMAGE_TAG
    ```

    This command does not deploy the code location but just updates the local state in `DAGSTER_BUILD_STATEDIR`.

5.  Deploy to Dagster+:

    ```
    dg plus deploy
    ```

    This command updates the code locations in Dagster+. Once this finishes successfully, you should be able to see the code locations under the **Deployments** tab in Dagster+.

:::note

Creating branch deployments using the CLI requires some additional steps. For more information, see [Setting up branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments/setting-up-branch-deployments).

:::

</TabItem>
</Tabs>
