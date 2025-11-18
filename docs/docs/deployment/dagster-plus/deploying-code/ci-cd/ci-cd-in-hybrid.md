---
description: Implement CI/CD for your Dagster+ Hybrid deployment with GitHub or a non-GitHub CI/CD provider.
title: CI/CD in Dagster+ Hybrid
sidebar_position: 7220
tags: [dagster-plus-feature]
---

import UpdateGitHubActionVersion from '@site/docs/partials/_UpdateGitHubActionVersion.md';

:::note

This guide only applies to [Dagster+ Hybrid deployments](/deployment/dagster-plus/hybrid). For Serverless guidance, see [CI/CD in Serverless](/deployment/dagster-plus/deploying-code/ci-cd/ci-cd-in-serverless).

:::

You can configure CI/CD for your project using GitHub or a non-GitHub CI/CD provider.

- If you use [GitHub](#github) as a CI/CD provider, you can use `dg` CLI to scaffold a GitHub Actions workflow YAML file.
- If you use a [non-GitHub CI/CD provider](#non-github), you can configure CI/CD using the `dg` CLI.

:::info

This guide assumes you have an existing Dagster project and have not already scaffolded a GitHub Actions workflow file. For project creation steps, see [Creating Dagster projects](/guides/build/projects/creating-projects).

:::

## GitHub

### Step 1. Generate the GitHub Actions workflow YAML file

To set up continuous integration using GitHub Actions, you can use the [`dg plus deploy configure CLI command`](/api/clis/dg-cli/dg-plus#deploy) to generate the GitHub workflow YAML file:

```shell
dg plus deploy configure --git-provider github
```

### Step 2. Configure the GitHub workflow YAML file

The GitHub workflow deploys your code to Dagster+ using these steps:

- **Initialize:** Your code is checked out and `build.yaml` file is validated. (**Note:** In older projects, this may be a `dagster_cloud.yaml` file.)
- **Docker image push:** A Docker image is built from your code and uploaded to your container registry.
- **Deploy to Dagster+** The code locations in Dagster+ are updated to use the new Docker image.

To configure the workflow:

1. In the repository, set the `DAGSTER_CLOUD_API_TOKEN` GitHub action secret to the Dagster+ agent token. See [Managing agent tokens in Dagster+](/deployment/dagster-plus/management/tokens/agent-tokens). For more information on GitHub Action Secrets, see the [GitHub documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets#creating-encrypted-secrets-for-a-repository).
2. In your `dagster-cloud-deploy.yml` workflow file, do the following:

- Set the `DAGSTER_CLOUD_ORGANIZATION` environment variable to your Dagster+ organization name.
- Uncomment the step that is relevant to your Docker container registry. For example, if using DockerHub, uncomment the DockerHub step. Make sure you have set up the relevant secrets for building and uploading your Docker images.

After you make the above changes and commit the workflow file, the CI process should be triggered to deploy your GitHub repository to Dagster+.

During the deployment, the agent will attempt to load your code and update the metadata in Dagster+. When that has finished, you should see the GitHub Action complete successfully, and also be able to see the code location under the **Deployment** tag in Dagster+.

<UpdateGitHubActionVersion />

## Non-GitHub CI/CD provider \{#non-github}

If you are using a non-GitHub CI/CD provider, your system should use the [`dg deploy` command](/api/clis/dg-cli/dg-plus#deploy) to deploy code locations to Dagster+.

{/* TODO add step 2 below for running `dg` equivalent of `dagster-cloud ci check --project-dir=. */}

1. Set the build environment variables. Note that all variables are required:
   - `DAGSTER_CLOUD_ORGANIZATION`: The name of your organization in Dagster+.
   - `DAGSTER_CLOUD_API_TOKEN`: A Dagster+ API token. **Note:** This is a sensitive value and should be stored as a CI/CD secret if possible.
   - `DAGSTER_BUILD_STATEDIR`: A path to a blank or non-existent temporary directory on the build machine that will be used to store local state during the build.
2. Initialize the build session:
   ```
    dg plus deploy start --deployment=DEPLOYMENT_NAME --project-dir=.
   ```
   This reads the `build.yaml` configuration and initializes the DAGSTER_BUILD_STATEDIR.
   ```

   ```
3. Build and upload Docker images for your code locations.

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

4. Update the build session with the Docker image tag. For each code location you want to deploy, run the following command passing the `IMAGE_TAG` used in the previous step:

   ```
   dg plus deploy set-build-output --location-name=code-location-a --image-tag=IMAGE_TAG
   ```

   This command does not deploy the code location but just updates the local state in `DAGSTER_BUILD_STATEDIR`.

5. Deploy to Dagster+:

   ```
   dg plus deploy
   ```

   This command updates the code locations in Dagster+. Once this finishes successfully, you should be able to see the code locations under the **Deployments** tab in Dagster+.

:::note

Creating branch deployments using the CLI requires some additional steps. For more information, see [Setting up branch deployments](/deployment/dagster-plus/deploying-code/branch-deployments/setting-up-branch-deployments).

:::
