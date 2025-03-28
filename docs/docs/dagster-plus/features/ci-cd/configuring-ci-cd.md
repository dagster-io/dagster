---
title: 'Configuring CI/CD for your project'
---

:::note

This article only applies to [Dagster+ Hybrid deployments](/dagster-plus/deployment/deployment-types/hybrid/).

:::

You can configure CI/CD for your project using GitHub or a non-GitHub CI/CD provider.

- If you use [GitHub](#github) as a CI/CD provider, you can use our GitHub Actions workflow to set up CI/CD for your project.
- If you use a [non-GitHub CI/CD provider](#non-github), you can configure CI/CD using the `dagster-cloud CLI`.

## GitHub

To set up continuous integration using GitHub Actions, you can the Dagster+ Hybrid Quickstart template, which is a template with everything you need to get started using Hybrid deployment in Dagster+, or you can use your own code.

- **If using the template:** Clone the [template repository](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart).
- **If using your own code:** Copy the [GitHub workflow file](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/tree/main/.github/workflows) from the template repository and add it to your repository.

### Configure the GitHub workflow YAML file

The GitHub workflow deploys your code to Dagster+ using these steps:

- **Initialize:** Your code is checked out and `dagster_cloud.yaml` file is validated.
- **Docker image push:** A Docker image is built from your code and uploaded to your container registry.
- **Deploy to Dagster+** The code locations in Dagster+ are updated to use the new Docker image.

To configure the workflow:

1. In the repository, set the `DAGSTER_CLOUD_API_TOKEN` GitHub action secret to the Dagster+ agent token. See "[Managing agent tokens in Dagster+](/dagster-plus/deployment/management/tokens/agent-tokens)". For more information on GitHub Action Secrets, see the [GitHub documentation](https://docs.github.com/en/actions/security-guides/encrypted-secrets#creating-encrypted-secrets-for-a-repository).
2. In your [`dagster-cloud-deploy.yml`](https://github.com/dagster-io/dagster-cloud-hybrid-quickstart/blob/main/.github/workflows/dagster-cloud-deploy.yml), set the DAGSTER_CLOUD_ORGANIZATION environment variable to your Dagster+ organization name.
3. In your `dagster-cloud-deploy.yml`, uncomment the step that is relevant to your Docker container registry. For example, if using DockerHub, uncomment the DockerHub step. Make sure you have set up the relevant secrets for building and uploading your Docker images.

After you make the above changes and commit the workflow file, the CI process should be triggered to deploy your GitHub repository to Dagster+.

During the deployment, the agent will attempt to load your code and update the metadata in Dagster+. When that has finished, you should see the GitHub Action complete successfully, and also be able to see the code location under the **Deployment** tag in Dagster+.

## Non-GitHub CI/CD provider \{#non-github}

If you are using a non-GitHub CI/CD provider, your system should use the `dagster-cloud ci` command to deploy code locations to Dagster+.

1. Set the build environment variables. Note that all variables are required:
   - `DAGSTER_CLOUD_ORGANIZATION`: The name of your organization in Dagster+.
   - `DAGSTER_CLOUD_API_TOKEN`: A Dagster+ API token. **Note:** This is a sensitive value and should be stored as a CI/CD secret if possible.
   - `DAGSTER_BUILD_STATEDIR`: A path to a blank or non-existent temporary directory on the build machine that will be used to store local state during the build.
2. Run the configuration check:
   ```
   dagster-cloud ci check --project-dir=.
   ```
   This is an optional step but useful to validate the contents of your dagster_cloud.yaml and connection to Dagster+.
3. Initialize the build session:
   ```
   dagster-cloud ci init --project-dir=.
   ```
   This reads the dagster_cloud.yaml configuration and initializes the DAGSTER_BUILD_STATEDIR.
4. Build and upload Docker images for your code locations.

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

   The upload step is specific to your Docker container registry and will require authentication. The only requirement is that the registry you upload to must match the registry specified in `dagster_cloud.yaml`.

5. Update the build session with the Docker image tag. For each code location you want to deploy, run the following command passing the `IMAGE_TAG` used in the previous step:

   ```
   dagster-cloud ci set-build-output --location-name=code-location-a --image-tag=IMAGE_TAG
   ```

   This command does not deploy the code location but just updates the local state in `DAGSTER_BUILD_STATEDIR`.

6. Deploy to Dagster+:

   ```
   dagster-cloud ci deploy
   ```

   This command updates the code locations in Dagster+. Once this finishes successfully, you should be able to see the code locations under the **Deployments** tab in Dagster+.

:::note

Creating branch deployments using the CLI requires some additional steps. For more information, see "[Using branch deployments with the dagster-cloud CLI](/dagster-plus/features/ci-cd/branch-deployments/using-branch-deployments-with-the-cli).
:::
