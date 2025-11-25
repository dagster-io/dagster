---
description: Implement CI/CD for your Dagster+ Hybrid deployment with GitHub or a non-GitHub CI/CD provider.
title: CI/CD in Dagster+ Hybrid
sidebar_position: 7220
tags: [dagster-plus-feature]
---

import UpdateGitHubActionVersion from '@site/docs/partials/_UpdateGitHubActionVersion.md';
import GitHubPrereqs from '@site/docs/partials/_GitHubPrereqs.md';
import GitLabPrereqs from '@site/docs/partials/_GitLabPrereqs.md';

:::note

This guide only applies to [Dagster+ Hybrid deployments](/deployment/dagster-plus/hybrid). For Serverless guidance, see [CI/CD in Serverless](/deployment/dagster-plus/deploying-code/ci-cd/ci-cd-in-serverless).

:::

Follow the steps below to create a GitHub or GitLab CI/CD configuration file in your project to deploy and synchronize your code to Dagster+ Hybrid. You can also use other Git providers, or a local Git repository with the [`dg plus` CLI](/api/clis/dg-cli/dg-plus) to run your own CI/CD process.

<Tabs>
   <TabItem value="github" label="GitHub">

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

   </TabItem>
   <TabItem value="gitlab" label="GitLab">

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

   </TabItem>
   <TabItem value="other" label="Other Git providers or local development">

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
